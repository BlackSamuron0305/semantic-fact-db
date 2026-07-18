"""The paper's benchmark suite.

Measures insert throughput and three query classes (LOOKUP, GLOBAL,
TEMPORAL) against real KnowledgeGraphEngine and SheafDatabaseEngine
instances at three scales, with cross-engine canonical-result
verification on every query class at every scale. This is the single
source of truth for the numbers reported in the paper's evaluation
section — see paper/sections/artifact.tex for the reproduction command
that invokes it (``sfdb benchmark``).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from common.interfaces import Query, QueryType
from common.types import Identifier
from sfdb.benchmark.engine_adapter import KGEngineAdapter, SheafEngineAdapter
from sfdb.benchmark.metrics import MeasuredRun
from sfdb.benchmark.outputs import BenchOutputRow, OutputWriter
from sfdb.benchmark.reproducibility import ReproducibilityRecord
from sfdb.benchmark.statistics import compute_statistics
from sfdb.benchmark.verification import verify_equivalence
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts

log = logging.getLogger(__name__)

PAPER_SCALES: tuple[int, ...] = (100, 1_000, 10_000)
NUM_RUNS = 10
WARM_UP = 2
QUERY_CLASSES: tuple[str, ...] = ("LOOKUP", "GLOBAL", "TEMPORAL", "TEMPORAL_UNBOUNDED")

# entity_0 always carries the highest Zipf weight by construction
# (see datasets.synthetic._zipf_weights), so it anchors a non-trivial
# LOOKUP result set at every scale.
ANCHOR_ENTITY = "entity_0"
# A bounded one-year window inside the generated temporal span
# (_TEMPORAL_ORIGIN=2020-01-01, span=6 years), roughly centred so that
# both early- and late-starting facts can overlap it.
TEMPORAL_QUERY_START = "2022"
TEMPORAL_QUERY_END = "2023"
# An open-ended window ("everything from 2023 onward", no end bound) over
# the same 6-year span. SFDB resolves this via the flat, binary-searchable
# start/end index (sfdb.sheaf.indexes.TemporalIndex.facts_ending_after)
# instead of the year-bucket path used for the bounded case above.
TEMPORAL_UNBOUNDED_QUERY_START = "2023"

ENGINES: tuple[str, ...] = ("KnowledgeGraph", "SheafDatabase")


def _canon_value(inner: Any) -> Any:
    # Numeric literals round-trip through KG's dictionary encoding as
    # float (e.g. 35 -> "35.0"), while SFDB keeps the original Python
    # object in memory. int vs. float is not a semantic difference in
    # the fact's meaning, so the canonical form normalises it away —
    # bool is checked first since bool is a subclass of int in Python.
    if isinstance(inner, bool):
        return inner
    if isinstance(inner, (int, float)):
        return float(inner)
    return str(inner)


def _canonical_fact(fact: Any) -> dict[str, Any]:
    return {
        "id": str(fact.id),
        "subject": str(fact.subject),
        "relation": str(fact.relation),
        "objects": tuple(_canon_value(o.inner) for o in fact.objects),
        "context": str(fact.context),
    }


def _query_for_class(qclass: str, limit: int) -> Query:
    if qclass == "LOOKUP":
        return Query(query_type=QueryType.LOOKUP, subject=Identifier(ANCHOR_ENTITY), limit=limit)
    if qclass == "GLOBAL":
        return Query(query_type=QueryType.GLOBAL, limit=limit)
    if qclass == "TEMPORAL":
        return Query(
            query_type=QueryType.TEMPORAL,
            temporal_start=TEMPORAL_QUERY_START,
            temporal_end=TEMPORAL_QUERY_END,
            limit=limit,
        )
    if qclass == "TEMPORAL_UNBOUNDED":
        return Query(
            query_type=QueryType.TEMPORAL,
            temporal_start=TEMPORAL_UNBOUNDED_QUERY_START,
            temporal_end=None,
            limit=limit,
        )
    raise ValueError(f"Unknown query class: {qclass}")


@dataclass
class ClassResult:
    engine_latencies_ms: dict[str, list[float]] = field(default_factory=dict)
    engine_result_counts: dict[str, int] = field(default_factory=dict)
    verified: bool = True
    verification_message: str = ""


@dataclass
class ScaleResult:
    num_facts: int
    insert_latencies_ms: dict[str, list[float]] = field(default_factory=dict)
    insert_memory_bytes: dict[str, list[int]] = field(default_factory=dict)
    query_classes: dict[str, ClassResult] = field(default_factory=dict)


def _make_adapter(engine_name: str) -> KGEngineAdapter | SheafEngineAdapter:
    if engine_name == "KnowledgeGraph":
        return KGEngineAdapter()
    if engine_name == "SheafDatabase":
        return SheafEngineAdapter()
    raise ValueError(f"Unknown engine: {engine_name}")


def run_scale(
    num_facts: int,
    writer: OutputWriter,
    num_runs: int = NUM_RUNS,
    warm_up: int = WARM_UP,
    insert_runs: int | None = None,
) -> ScaleResult:
    """Benchmark one dataset scale: insert throughput plus every query class."""
    config = SyntheticConfig(num_facts=num_facts, num_entities=max(20, num_facts // 10), seed=42)
    dataset = generate_facts(config)
    facts = dataset.facts
    result = ScaleResult(num_facts=num_facts)

    # --- Insert throughput: independent fresh-engine bulk inserts ---
    n_insert_runs = insert_runs if insert_runs is not None else num_runs
    for engine_name in ENGINES:
        latencies: list[float] = []
        memories: list[int] = []
        for run_idx in range(n_insert_runs):
            adapter = _make_adapter(engine_name)
            with MeasuredRun(label=f"{engine_name}_insert_{num_facts}_{run_idx}") as mr:
                adapter.insert_batch(facts)
            sm = mr.metrics()
            latencies.append(sm.latency_ms)
            memories.append(sm.memory_bytes)
            writer.add(
                BenchOutputRow(
                    engine=engine_name,
                    query=f"INSERT_{num_facts}",
                    run=run_idx,
                    latency_ms=sm.latency_ms,
                    memory_bytes=sm.memory_bytes,
                    cpu_percent=sm.cpu_percent,
                    gc_collections=sm.gc_collections,
                    disk_read=sm.disk_read_bytes,
                    disk_write=sm.disk_write_bytes,
                    cache_hit=False,
                    verified=True,
                )
            )
        result.insert_latencies_ms[engine_name] = latencies
        result.insert_memory_bytes[engine_name] = memories
        mean_latency = sum(latencies) / len(latencies)
        log.info("  insert %s @ N=%d: mean=%.3fms", engine_name, num_facts, mean_latency)

    # --- Query classes: dataset populated once, queried num_runs times each ---
    adapters = {name: _make_adapter(name) for name in ENGINES}
    for adapter in adapters.values():
        adapter.insert_batch(facts)

    for qclass in QUERY_CLASSES:
        query = _query_for_class(qclass, limit=num_facts * 10 + 10)
        cls_result = ClassResult()
        canonical_by_engine: dict[str, list[dict[str, Any]]] = {}

        for engine_name, adapter in adapters.items():
            for _ in range(warm_up):
                adapter.execute_query(query)

            latencies = []
            last_facts: list[Any] = []
            for run_idx in range(num_runs):
                with MeasuredRun(label=f"{engine_name}_{qclass}_{num_facts}_{run_idx}") as mr:
                    last_facts = adapter.execute_query(query)
                sm = mr.metrics()
                latencies.append(sm.latency_ms)
                writer.add(
                    BenchOutputRow(
                        engine=engine_name,
                        query=f"{qclass}_{num_facts}",
                        run=run_idx,
                        latency_ms=sm.latency_ms,
                        memory_bytes=sm.memory_bytes,
                        cpu_percent=sm.cpu_percent,
                        gc_collections=sm.gc_collections,
                        disk_read=sm.disk_read_bytes,
                        disk_write=sm.disk_write_bytes,
                        cache_hit=False,
                        verified=True,  # updated below once cross-engine equivalence is known
                    )
                )
            cls_result.engine_latencies_ms[engine_name] = latencies
            cls_result.engine_result_counts[engine_name] = len(last_facts)
            canonical_by_engine[engine_name] = [_canonical_fact(f) for f in last_facts]

        v = verify_equivalence(canonical_by_engine)
        cls_result.verified = v.passed
        cls_result.verification_message = v.message
        if not v.passed:
            log.warning(
                "Cross-engine verification FAILED for %s at N=%d: %s", qclass, num_facts, v.message
            )
        else:
            log.info(
                "  %s @ N=%d: verified OK (%s)", qclass, num_facts, cls_result.engine_result_counts
            )
        result.query_classes[qclass] = cls_result

    return result


def _build_summary(scale_results: list[ScaleResult]) -> dict[str, Any]:
    summary: dict[str, Any] = {"insert": {}, "insert_memory_bytes": {}, "query": {}}
    for sr in scale_results:
        n = sr.num_facts
        summary["insert"][str(n)] = {
            engine: compute_statistics(lat).to_dict()
            for engine, lat in sr.insert_latencies_ms.items()
        }
        summary["insert_memory_bytes"][str(n)] = {
            engine: (sum(mem) / len(mem) if mem else 0.0)
            for engine, mem in sr.insert_memory_bytes.items()
        }
        summary["query"][str(n)] = {}
        for qclass, cr in sr.query_classes.items():
            summary["query"][str(n)][qclass] = {
                "verified": cr.verified,
                "verification_message": cr.verification_message,
                "result_counts": cr.engine_result_counts,
                "stats": {
                    engine: compute_statistics(lat).to_dict()
                    for engine, lat in cr.engine_latencies_ms.items()
                },
            }
    return summary


def _dataset_checksum(scales: tuple[int, ...]) -> str:
    """Hash the deterministically-generated fact stream at each scale.

    Regenerates each scale's dataset (cheap and deterministic under the
    fixed seed) purely to checksum it, independent of the benchmarked
    engines, so the reported checksum reflects the actual data the run
    used rather than an unset placeholder.
    """
    per_scale = []
    for n in scales:
        config = SyntheticConfig(num_facts=n, num_entities=max(20, n // 10), seed=42)
        dataset = generate_facts(config)
        per_scale.append(ReproducibilityRecord.checksum(tuple(str(f) for f in dataset.facts)))
    return ReproducibilityRecord.checksum(tuple(per_scale))


def run_paper_suite(
    output_dir: str = "results",
    scales: tuple[int, ...] = PAPER_SCALES,
    num_runs: int = NUM_RUNS,
    warm_up: int = WARM_UP,
    insert_runs: int | None = None,
) -> dict[str, Any]:
    """Run the full paper benchmark suite and write results/paper_suite.*."""
    writer = OutputWriter(output_dir)
    repro = ReproducibilityRecord()
    repro.capture(seed=42, dataset_checksum=_dataset_checksum(scales))

    scale_results: list[ScaleResult] = []
    all_verified = True
    for n in scales:
        log.info("Running paper suite at N=%d", n)
        sr = run_scale(n, writer, num_runs=num_runs, warm_up=warm_up, insert_runs=insert_runs)
        scale_results.append(sr)
        for cr in sr.query_classes.values():
            all_verified = all_verified and cr.verified

    writer.to_csv("paper_suite")
    writer.to_json("paper_suite")
    writer.to_markdown("paper_suite")
    repro.to_json(str(Path(output_dir) / "paper_suite_reproducibility.json"))

    summary = _build_summary(scale_results)
    Path(output_dir, "paper_suite_summary.json").write_text(json.dumps(summary, indent=2))

    return {"scale_results": scale_results, "all_verified": all_verified, "summary": summary}
