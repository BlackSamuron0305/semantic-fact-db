"""Contextual benchmark runner — orchestrates all C1-C10 benchmarks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sfdb.benchmark.contextual.benchmarks import (
    ContextualBenchResult,
    benchmark_consistency,
    benchmark_event_reconstruction,
    benchmark_global_section,
    benchmark_high_arity,
    benchmark_high_arity_join,
    benchmark_lineage,
    benchmark_mixed_workload,
    benchmark_neighborhood,
    benchmark_provenance,
    benchmark_temporal,
    benchmark_temporal_aggregation,
)
from sfdb.benchmark.contextual.fairness import (
    FairnessEntry,
    FairnessReport,
    verify_knowledge_graph_parity,
)
from sfdb.benchmark.contextual.generator import (
    ContextualConfig,
    ContextualDataset,
    generate_contextual_dataset,
)
from sfdb.benchmark.contextual.metrics import ContextualMetrics
from sfdb.benchmark.contextual.reporter import ContextualBenchReporter
from sfdb.benchmark.contextual.workloads import ALL_CONTEXTUAL_WORKLOADS, WORKLOAD_BY_ID


@dataclass
class ContextualBenchConfig:
    dataset_size: str = "medium"
    num_entities: int = 1000
    num_high_arity_facts: int = 5000
    num_temporal_facts: int = 5000
    num_provenance_facts: int = 2000
    num_contextual_facts: int = 5000
    high_arity_relations: tuple[int, ...] = (3, 5, 8)
    temporal_range: tuple[int, int] = (0, 100000)
    provenance_max_depth: int = 8
    seed: int = 42
    output_dir: str = "results/contextual"
    workloads: tuple[str, ...] = ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10")
    num_runs: int = 5
    num_warmup: int = 2


class ContextualBenchRunner:
    def __init__(self, config: ContextualBenchConfig) -> None:
        self.config = config
        self.dataset: ContextualDataset | None = None
        self.reporter = ContextualBenchReporter()
        self.fairness_entries: list[FairnessEntry] = []

    def generate_dataset(self) -> ContextualDataset:
        cfg = ContextualConfig(
            seed=self.config.seed,
            num_entities=self.config.num_entities,
            num_high_arity_facts=self.config.num_high_arity_facts,
            num_temporal_facts=self.config.num_temporal_facts,
            num_provenance_facts=self.config.num_provenance_facts,
            num_contextual_facts=self.config.num_contextual_facts,
            high_arity_relations=list(self.config.high_arity_relations),
            temporal_range=self.config.temporal_range,
            provenance_max_depth=self.config.provenance_max_depth,
        )
        self.dataset = generate_contextual_dataset(cfg)
        return self.dataset

    def run(self) -> ContextualBenchReporter:
        if self.dataset is None:
            self.generate_dataset()

        ds = self.dataset
        benchmark_fns = {
            "C1": lambda kw: benchmark_event_reconstruction(ds, **kw),
            "C2": lambda kw: benchmark_neighborhood(ds, **kw),
            "C3": lambda kw: benchmark_high_arity(ds, **kw),
            "C4": lambda kw: benchmark_high_arity_join(ds, **kw),
            "C5": lambda kw: benchmark_temporal(ds, **kw),
            "C6": lambda kw: benchmark_temporal_aggregation(ds, **kw),
            "C7": lambda kw: benchmark_provenance(ds, **kw),
            "C8": lambda kw: benchmark_consistency(ds, **kw),
            "C9": lambda kw: benchmark_global_section(ds, **kw),
            "C10": lambda kw: benchmark_mixed_workload(ds, **kw),
        }

        for wid in self.config.workloads:
            fn = benchmark_fns.get(wid)
            if fn is None:
                continue
            for run_idx in range(self.config.num_runs):
                bm = fn({"run": run_idx})
                kg_result = bm.run_kg()
                sheaf_result = bm.run_sheaf()
                self.reporter.add(kg_result)
                self.reporter.add(sheaf_result)
                workload = WORKLOAD_BY_ID.get(wid)
                if workload:
                    entry = verify_knowledge_graph_parity(
                        workload, kg_result.raw_results, sheaf_result.raw_results,
                    )
                    self.fairness_entries.append(entry)

        return self.reporter

    def export(self) -> dict[str, str]:
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        md_path = output_dir / "contextual_report.md"
        md_path.write_text(self.reporter.to_markdown(), encoding="utf-8")

        json_path = output_dir / "contextual_report.json"
        json_path.write_text(
            json.dumps({"results": self.reporter.to_dict(), "fairness": self._fairness_dict()}, indent=2),
            encoding="utf-8",
        )

        return {"markdown": str(md_path), "json": str(json_path)}

    def _fairness_dict(self) -> dict[str, Any]:
        return {
            "all_executable": all(e.kg_executable and e.sheaf_executable for e in self.fairness_entries),
            "all_equivalent": all(e.results_equivalent for e in self.fairness_entries if e.results_equivalent is not None),
            "entries": [
                {
                    "workload_id": e.workload_id,
                    "kg_executable": e.kg_executable,
                    "sheaf_executable": e.sheaf_executable,
                    "results_equivalent": e.results_equivalent,
                }
                for e in self.fairness_entries
            ],
        }


def run_contextual_suite(config: ContextualBenchConfig | None = None) -> ContextualBenchReporter:
    if config is None:
        config = ContextualBenchConfig()
    runner = ContextualBenchRunner(config)
    runner.generate_dataset()
    reporter = runner.run()
    runner.export()
    return reporter
