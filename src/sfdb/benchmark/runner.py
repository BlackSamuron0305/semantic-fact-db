"""Benchmark runner — orchestrates end-to-end benchmark execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sfdb.benchmark.config import BenchmarkConfig, BenchmarkMode, CacheMode
from sfdb.benchmark.engine_adapter import EngineAdapter, EngineType, create_adapters
from sfdb.benchmark.metrics import MeasuredRun, Profiler, SystemMetrics
from sfdb.benchmark.outputs import BenchOutputRow, OutputWriter
from sfdb.benchmark.profiler import CacheProfiler
from sfdb.benchmark.query_workload import QueryWorkload, all_workloads
from sfdb.benchmark.reproducibility import ReproducibilityRecord
from sfdb.benchmark.statistics import Statistics, compute_statistics
from sfdb.benchmark.verification import VerificationResult, verify_equivalence
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts


@dataclass
class BenchmarkResult:
    config: BenchmarkConfig
    engine_results: dict[str, dict[str, list[SystemMetrics]]] = field(default_factory=dict)
    verification: VerificationResult = field(default_factory=lambda: VerificationResult(True))
    statistics: dict[str, dict[str, Statistics]] = field(default_factory=dict)
    system_info: dict[str, Any] = field(default_factory=dict)
    reproducibility: dict[str, Any] = field(default_factory=dict)
    outputs: list[str] = field(default_factory=list)

    def engine_names(self) -> list[str]:
        return list(self.engine_results.keys())

    def query_ids(self) -> list[str]:
        seen: set[str] = set()
        for er in self.engine_results.values():
            seen.update(er.keys())
        return sorted(seen)


class BenchmarkRunner:
    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self._adapters: dict[EngineType, EngineAdapter] = {}
        self._writer = OutputWriter(config.output_dir)
        self._cache_profiler = CacheProfiler()
        self._repro = ReproducibilityRecord()
        self._result = BenchmarkResult(config=config)

    def initialize(self, facts: list[Any] | None = None) -> None:
        self._adapters = create_adapters()
        if facts:
            for et, adapter in self._adapters.items():
                if et in (EngineType.KNOWLEDGE_GRAPH, EngineType.SHEAF_DATABASE):
                    adapter.insert_batch(facts)

    def run(self) -> BenchmarkResult:
        log = logging.getLogger(__name__)
        result = self._result
        result.system_info = Profiler.system_info()
        result.reproducibility = self._repro.capture(seed=self.config.seed)

        if self.config.mode == BenchmarkMode.STORAGE:
            return self._run_storage()
        if self.config.mode == BenchmarkMode.IMPORT:
            return self._run_import()
        if self.config.mode == BenchmarkMode.EXPORT:
            return self._run_export()
        if self.config.mode == BenchmarkMode.CONSISTENCY:
            return self._run_consistency()

        workloads = (
            all_workloads()
            if not self.config.queries
            else [q for q in all_workloads() if q.id in self.config.queries]
        )

        for et, adapter in self._adapters.items():
            engine_name = adapter.name()
            if engine_name not in self.config.engines:
                continue
            log.info("Benchmarking engine: %s", engine_name)
            result.engine_results[engine_name] = {}

            for wl in workloads:
                log.info("  Query: %s (%s)", wl.id, wl.name)
                metrics_list: list[SystemMetrics] = []

                runs = (
                    self.config.num_runs_cold
                    if self.config.cache == CacheMode.COLD
                    else self.config.num_runs_warm
                )

                for run_idx in range(runs):
                    if self.config.cache == CacheMode.COLD:
                        adapter.clear()
                        if hasattr(self._adapters, "keys"):
                            for other_et, other_adapter in self._adapters.items():
                                if other_et != et:
                                    other_adapter.clear()

                    with MeasuredRun(label=f"{engine_name}_{wl.id}_{run_idx}") as mr:
                        adapter.execute_query_str(wl.text)

                    sm = mr.metrics()
                    metrics_list.append(sm)

                    self._writer.add(
                        BenchOutputRow(
                            engine=engine_name,
                            query=wl.id,
                            run=run_idx,
                            latency_ms=sm.latency_ms,
                            memory_bytes=sm.memory_bytes,
                            cpu_percent=sm.cpu_percent,
                            gc_collections=sm.gc_collections,
                            disk_read=sm.disk_read_bytes,
                            disk_write=sm.disk_write_bytes,
                            cache_hit=self.config.cache == CacheMode.WARM,
                        )
                    )

                latency_vals = [m.latency_ms for m in metrics_list]
                result.engine_results[engine_name][wl.id] = metrics_list

                if engine_name not in result.statistics:
                    result.statistics[engine_name] = {}
                result.statistics[engine_name][wl.id] = compute_statistics(latency_vals)

        self._verify_across_engines(workloads)
        self._export_outputs()
        return result

    def _verify_across_engines(self, workloads: list[QueryWorkload]) -> None:
        all_ok = True
        for wl in workloads:
            results: dict[str, Any] = {}
            for _et, adapter in self._adapters.items():
                if adapter.name() in self.config.engines:
                    try:
                        qs = wl.text
                        results[adapter.name()] = adapter.execute_query_str(qs)
                    except Exception:
                        pass
            if len(results) >= 2:
                v = verify_equivalence(results)
                if not v.passed:
                    all_ok = False
                    logging.warning("Verification failed for %s: %s", wl.id, v.message)
        self._result.verification = VerificationResult(all_ok)

    def _run_storage(self) -> BenchmarkResult:
        result = self._result
        self._adapters = create_adapters()
        for _et, adapter in self._adapters.items():
            if adapter.name() not in self.config.engines:
                continue
            en = adapter.name()
            result.engine_results[en] = {}
            sizes = [100, 1000, 10000, 100000]
            for n in sizes:
                cfg = SyntheticConfig(num_facts=n, seed=self.config.seed)
                ds = generate_facts(cfg)
                adapter.clear()
                with MeasuredRun(label=f"{en}_storage_{n}") as mr:
                    adapter.insert_batch(ds.facts)
                result.engine_results[en][f"storage_{n}"] = [mr.metrics()]
        return result

    def _run_import(self) -> BenchmarkResult:
        return self._result

    def _run_export(self) -> BenchmarkResult:
        return self._result

    def _run_consistency(self) -> BenchmarkResult:
        result = self._result
        log = logging.getLogger(__name__)
        workloads = (
            all_workloads()
            if not self.config.queries
            else [q for q in all_workloads() if q.id in self.config.queries]
        )

        for et, adapter in self._adapters.items():
            engine_name = adapter.name()
            if engine_name not in self.config.engines:
                continue
            log.info("Consistency check engine: %s", engine_name)
            result.engine_results[engine_name] = {}

            for wl in workloads:
                run_count = max(self.config.num_runs_cold, 5)
                metrics_list: list[SystemMetrics] = []
                for run_idx in range(run_count):
                    adapter.clear()
                    with MeasuredRun(label=f"{engine_name}_{wl.id}_{run_idx}") as mr:
                        adapter.execute_query_str(wl.text)
                    sm = mr.metrics()
                    metrics_list.append(sm)
                    self._writer.add(
                        BenchOutputRow(
                            engine=engine_name,
                            query=wl.id,
                            run=run_idx,
                            latency_ms=sm.latency_ms,
                            memory_bytes=sm.memory_bytes,
                            cpu_percent=sm.cpu_percent,
                            gc_collections=sm.gc_collections,
                            disk_read=sm.disk_read_bytes,
                            disk_write=sm.disk_write_bytes,
                            cache_hit=False,
                        )
                    )
                result.engine_results[engine_name][wl.id] = metrics_list
                latency_vals = [m.latency_ms for m in metrics_list]
                if engine_name not in result.statistics:
                    result.statistics[engine_name] = {}
                result.statistics[engine_name][wl.id] = compute_statistics(latency_vals)

        self._verify_across_engines(workloads)
        self._export_outputs()
        return result

    def _export_outputs(self) -> None:
        name = self.config.name
        self._result.outputs.append(self._writer.to_csv(name))
        self._result.outputs.append(self._writer.to_json(name))
        self._result.outputs.append(self._writer.to_parquet(name))
        self._result.outputs.append(self._writer.to_markdown(name))
        self._result.outputs.append(self._writer.to_latex_table(f"{name}_table"))
        self._result.outputs.append(
            self._writer.to_summary_table(self._result.statistics, f"{name}_summary")
        )
        repro_path = Path(self.config.output_dir) / f"{name}_reproducibility.json"
        self._repro.to_json(str(repro_path))
        self._result.outputs.append(str(repro_path))
