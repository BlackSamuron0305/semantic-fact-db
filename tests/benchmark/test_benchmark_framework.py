"""Tests for the benchmark framework."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from sfdb.benchmark.config import BenchmarkConfig, BenchmarkMode, CacheMode
from sfdb.benchmark.engine_adapter import (
    EngineType,
    KGEngineAdapter,
    SheafEngineAdapter,
    create_adapters,
)
from sfdb.benchmark.metrics import MeasuredRun, Profiler, SystemMetrics
from sfdb.benchmark.outputs import BenchOutputRow, OutputWriter
from sfdb.benchmark.profiler import CacheProfiler
from sfdb.benchmark.query_workload import all_workloads, benchmark_queries
from sfdb.benchmark.reproducibility import ReproducibilityRecord
from sfdb.benchmark.runner import BenchmarkResult, BenchmarkRunner
from sfdb.benchmark.statistics import compute_statistics
from sfdb.benchmark.verification import verify_equivalence
from sfdb.benchmark.visualization import VisualizationEngine
from sfdb.common.types import Context, Fact, Identifier, Value
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts


class TestBenchmarkConfig:
    def test_defaults(self) -> None:
        c = BenchmarkConfig()
        assert c.name == "benchmark"
        assert c.mode == BenchmarkMode.MICRO
        assert c.cache == CacheMode.COLD
        assert c.seed == 42

    def test_to_dict(self) -> None:
        c = BenchmarkConfig(name="test", num_runs_cold=10)
        d = c.to_dict()
        assert d["name"] == "test"
        assert d["num_runs_cold"] == 10


class TestEngineAdapter:
    def test_kg_adapter(self) -> None:
        a = KGEngineAdapter()
        assert "KnowledgeGraph" in a.name()

    def test_sheaf_adapter(self) -> None:
        a = SheafEngineAdapter()
        assert "Sheaf" in a.name()

    def test_create_adapters(self) -> None:
        adapters = create_adapters()
        assert EngineType.KNOWLEDGE_GRAPH in adapters
        assert EngineType.SHEAF_DATABASE in adapters

    def test_insert_and_clear(self) -> None:
        a = KGEngineAdapter()
        f = Fact(
            id=Identifier("f1"),
            subject=Identifier("s1"),
            relation=Identifier("r1"),
            objects=(Value.literal("o1"),),
            context=Context("world"),
        )
        a.insert(f)
        a.clear()
        r = a.execute_query_str("test")
        assert isinstance(r, list)


class TestMetrics:
    def test_system_metrics(self) -> None:
        sm = SystemMetrics(latency_ns=10_000_000, memory_bytes=1024, cpu_percent=5.0)
        assert sm.latency_ms == 10.0
        assert sm.memory_bytes == 1024

    def test_measured_run(self) -> None:
        with MeasuredRun("test") as mr:
            pass
        m = mr.metrics()
        assert m.latency_ms >= 0
        assert m.memory_bytes >= 0

    def test_profiler_system_info(self) -> None:
        info = Profiler.system_info()
        assert "cpu_count" in info


class TestQueryWorkload:
    def test_all_workloads(self) -> None:
        wls = all_workloads()
        assert len(wls) == 15

    def test_benchmark_queries_default(self) -> None:
        assert len(benchmark_queries) == 15

    def test_benchmark_queries_subset(self) -> None:
        ids = {q.id for q in benchmark_queries}
        assert "Q1" in ids
        assert "Q15" in ids

    def test_query_attributes(self) -> None:
        wl = all_workloads()[0]
        assert hasattr(wl, "text")
        assert wl.category == "lookup"


class TestVerification:
    def test_single_engine(self) -> None:
        v = verify_equivalence({"KG": [{"x": "1"}]})
        assert v.passed

    def test_equivalence_pass(self) -> None:
        r = verify_equivalence(
            {
                "KG": [{"x": "1"}, {"x": "2"}],
                "Sheaf": [{"x": "1"}, {"x": "2"}],
            }
        )
        assert r.passed

    def test_equivalence_fail(self) -> None:
        r = verify_equivalence(
            {
                "KG": [{"x": "1"}],
                "Sheaf": [{"x": "2"}],
            }
        )
        assert not r.passed


class TestStatistics:
    def test_empty(self) -> None:
        s = compute_statistics([])
        assert s.count == 0

    def test_basic(self) -> None:
        s = compute_statistics([10.0, 20.0, 30.0])
        assert s.count == 3
        assert s.mean == 20.0
        assert s.min_val == 10.0
        assert s.max_val == 30.0

    def test_percentiles(self) -> None:
        s = compute_statistics(list(range(1, 101)))
        assert s.count == 100
        assert 49 <= s.p50 <= 51
        assert s.p95 >= 90
        assert s.p99 >= 95

    def test_to_dict(self) -> None:
        s = compute_statistics([1.0, 2.0, 3.0])
        d = s.to_dict()
        assert d["count"] == 3


class TestOutputs:
    def test_output_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            w = OutputWriter(tmp)
            w.add(
                BenchOutputRow(
                    engine="KG",
                    query="Q1",
                    run=0,
                    latency_ms=1.0,
                    memory_bytes=0,
                    cpu_percent=0.0,
                    gc_collections=0,
                    disk_read=0,
                    disk_write=0,
                    cache_hit=False,
                )
            )
            p = w.to_csv("test")
            assert Path(p).exists()

    def test_csv_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            w = OutputWriter(tmp)
            w.add(
                BenchOutputRow(
                    engine="KG",
                    query="Q1",
                    run=0,
                    latency_ms=1.0,
                    memory_bytes=100,
                    cpu_percent=0.5,
                    gc_collections=0,
                    disk_read=0,
                    disk_write=0,
                    cache_hit=False,
                )
            )
            p = Path(w.to_csv("test"))
            text = p.read_text()
            assert "latency_ms" in text

    def test_latex_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            w = OutputWriter(tmp)
            w.add(
                BenchOutputRow(
                    engine="KG",
                    query="Q1",
                    run=0,
                    latency_ms=1.0,
                    memory_bytes=0,
                    cpu_percent=0.0,
                    gc_collections=0,
                    disk_read=0,
                    disk_write=0,
                    cache_hit=False,
                )
            )
            p = w.to_latex_table("test")
            content = Path(p).read_text()
            assert "\\begin{tabular}" in content

    def test_summary_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            w = OutputWriter(tmp)
            stats = {"KG": {"Q1": compute_statistics([1.0, 2.0])}}
            p = w.to_summary_table(stats, "test")
            content = Path(p).read_text()
            assert "mean" in content.lower()


class TestProfiler:
    def test_cache_profiler(self) -> None:
        p = CacheProfiler()
        p.record_hit()
        p.record_miss()
        assert p.hit_rate() == 0.5

    def test_cache_profiler_empty(self) -> None:
        p = CacheProfiler()
        assert p.hit_rate() == 0.0


class TestReproducibility:
    def test_capture(self) -> None:
        r = ReproducibilityRecord()
        d = r.capture(seed=42)
        assert "seed" in d
        assert "os" in d
        assert "python_version" in d

    def test_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = ReproducibilityRecord()
            r.capture(seed=42)
            path = Path(tmp) / "repro.json"
            r.to_json(str(path))
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["seed"] == 42


class TestVisualization:
    def test_engine_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            v = VisualizationEngine(tmp)
            paths = v.latency_plot({"KG": {"Q1": [1.0]}}, "test")
            assert isinstance(paths, list)

    def test_save_no_matplotlib(self) -> None:
        import sys

        matplotlib = sys.modules.get("matplotlib")
        if matplotlib is None:
            with tempfile.TemporaryDirectory() as tmp:
                v = VisualizationEngine(tmp)
                paths = v._save("test_plot")
                assert paths is None


class TestRunner:
    def test_benchmark_result(self) -> None:
        r = BenchmarkResult(config=BenchmarkConfig())
        assert r.engine_names() == []
        assert r.query_ids() == []

    def test_runner_initialize(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = BenchmarkConfig(output_dir=tmp)
            runner = BenchmarkRunner(cfg)
            f = Fact(
                id=Identifier("f1"),
                subject=Identifier("s1"),
                relation=Identifier("r1"),
                objects=(Value.literal("o1"),),
                context=Context("world"),
            )
            runner.initialize(facts=[f])
            assert len(runner._adapters) > 0

    def test_runner_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = BenchmarkConfig(
                output_dir=tmp, num_runs_cold=1, queries=("Q1",), engines=("KnowledgeGraph",)
            )
            runner = BenchmarkRunner(cfg)
            f = Fact(
                id=Identifier("f1"),
                subject=Identifier("s1"),
                relation=Identifier("r1"),
                objects=(Value.literal("o1"),),
                context=Context("world"),
            )
            runner.initialize(facts=[f])
            result = runner.run()
            assert result is not None


class TestDataset:
    def test_synthetic_generation(self) -> None:
        cfg = SyntheticConfig(num_facts=50, num_entities=10, seed=42)
        ds = generate_facts(cfg)
        assert len(ds.facts) == 50

    def test_synthetic_determinism(self) -> None:
        cfg = SyntheticConfig(num_facts=100, num_entities=20, seed=7)
        ds1 = generate_facts(cfg)
        ds2 = generate_facts(cfg)
        assert ds1.facts == ds2.facts

    def test_synthetic_events(self) -> None:
        cfg = SyntheticConfig(num_facts=200, num_entities=20, seed=42)
        ds = generate_facts(cfg)
        assert len(ds.facts) == 200
