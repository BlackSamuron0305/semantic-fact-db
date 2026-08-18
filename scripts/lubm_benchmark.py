#!/usr/bin/env python3
"""Standard-benchmark workload: run the paper's five query classes against
LUBM (Lehigh University Benchmark) data instead of this project's own
synthetic generator.

LUBM (sfdb.datasets.lubm.LUBMGenerator) is the de-facto standard
benchmark for RDF store evaluation, independent of both this project's
synthetic generator and the real-world Wikidata case study
(scripts/wikidata_case_study_benchmark.py) -- a third kind of dataset,
not just a third store. Scale is expressed the way the standard LUBM
benchmark itself expresses it, as a university count, not an exact fact
count; the four counts used here (1, 3, 26, 265 universities) were
chosen empirically to land close to this paper's usual 100/1,000/10,000/
100,000-fact scale points without forcing an exact match neither
LUBM's own generator nor a real deployment would produce.

The original LUBMGenerator carried no temporal data at all (no fact had
a `temporal` envelope), which made TEMPORAL and TEMPORAL_UNBOUNDED
vacuous no-ops on this dataset. It has since been extended with a
one-semester temporal envelope on `takesCourse` and `teacherOf` facts
(a student takes a course, or a professor teaches one, in a specific
academic term) spread across ten real years -- additive metadata that
does not change what LUBM's own standard Q1-Q14 query set would return,
since none of them reference it.

Runs the same three in-house engines (KnowledgeGraph, KnowledgeGraphMem,
SheafDatabase) and the same LOOKUP/GLOBAL/CONTEXT/TEMPORAL taxonomy as
sfdb.benchmark.paper_suite, with the same three-way cross-engine
canonical-result verification. Writes results/lubm_benchmark.json, which
scripts/generate_tables.py turns into paper/tables/lubm_benchmark.tex.

Usage: uv run python scripts/lubm_benchmark.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from common.interfaces import Query, QueryType
from common.types import Identifier
from sfdb.benchmark.engine_adapter import KGEngineAdapter, KGMemEngineAdapter, SheafEngineAdapter
from sfdb.benchmark.metrics import MeasuredRun
from sfdb.benchmark.statistics import compute_statistics
from sfdb.benchmark.verification import verify_equivalence
from sfdb.datasets.lubm import LUBMConfig, LUBMGenerator

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "results" / "lubm_benchmark.json"

NUM_RUNS = 10
WARM_UP = 2
ENGINES: tuple[str, ...] = ("KnowledgeGraph", "KnowledgeGraphMem", "SheafDatabase")
QUERY_CLASSES: tuple[str, ...] = ("LOOKUP", "GLOBAL", "CONTEXT", "TEMPORAL", "TEMPORAL_UNBOUNDED")

# University counts chosen to land close to this paper's usual four
# fact-count scales (100/1,000/10,000/100,000), not exact matches --
# see the module docstring.
UNIVERSITY_SCALES: tuple[int, ...] = (1, 3, 26, 265)

# LOOKUP_ANCHOR: University0's Department0's first ("Full") professor --
# guaranteed to exist at every scale under the fixed seed, since
# num_depts is always at least 2 and prof_idx == 0 is always assigned
# the "Full" title. Matches rdf:type, worksFor, headOf, and any courses
# they teach: a small, non-trivial, non-zero LOOKUP result at every
# scale.
LOOKUP_ANCHOR = "http://www.FullProfessor0.Department0.University0"
# CONTEXT_ANCHOR: University0's Department0 -- likewise guaranteed to
# exist at every scale.
CONTEXT_ANCHOR = "world.University0.dept0"
# A four-year window inside the ten-year (2015-2024) span
# takesCourse/teacherOf terms are drawn from.
TEMPORAL_QUERY_START = "2018-01-01T00:00:00+00:00"
TEMPORAL_QUERY_END = "2020-01-01T00:00:00+00:00"
TEMPORAL_UNBOUNDED_QUERY_START = "2022-01-01T00:00:00+00:00"


def _canonical_fact(fact: Any) -> dict[str, Any]:
    def _canon_value(inner: Any) -> Any:
        if isinstance(inner, bool):
            return inner
        if isinstance(inner, (int, float)):
            return float(inner)
        return str(inner)

    return {
        "id": str(fact.id),
        "subject": str(fact.subject),
        "relation": str(fact.relation),
        "objects": tuple(_canon_value(o.inner) for o in fact.objects),
        "context": str(fact.context),
    }


def _make_adapter(engine_name: str) -> KGEngineAdapter | SheafEngineAdapter:
    if engine_name == "KnowledgeGraph":
        return KGEngineAdapter()
    if engine_name == "KnowledgeGraphMem":
        return KGMemEngineAdapter()
    if engine_name == "SheafDatabase":
        return SheafEngineAdapter()
    raise ValueError(f"Unknown engine: {engine_name}")


def _query_for_class(qclass: str, limit: int) -> Query:
    if qclass == "LOOKUP":
        return Query(query_type=QueryType.LOOKUP, subject=Identifier(LOOKUP_ANCHOR), limit=limit)
    if qclass == "GLOBAL":
        return Query(query_type=QueryType.GLOBAL, limit=limit)
    if qclass == "CONTEXT":
        return Query(query_type=QueryType.CONTEXT, context=CONTEXT_ANCHOR, limit=limit)
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


def run_scale(num_universities: int) -> dict[str, Any]:
    facts = LUBMGenerator(LUBMConfig(num_universities=num_universities, seed=42)).generate()
    num_facts = len(facts)
    print(f"  {num_universities} universities -> {num_facts} facts")

    result: dict[str, Any] = {"num_universities": num_universities, "num_facts": num_facts}

    # --- Insert throughput: independent fresh-engine bulk inserts ---
    result["insert"] = {}
    for engine_name in ENGINES:
        latencies = []
        for run_idx in range(NUM_RUNS):
            adapter = _make_adapter(engine_name)
            with MeasuredRun(label=f"{engine_name}_insert_{run_idx}") as mr:
                adapter.insert_batch(facts)
            latencies.append(mr.metrics().latency_ms)
        result["insert"][engine_name] = compute_statistics(latencies).to_dict()

    # --- Query classes: dataset populated once, queried NUM_RUNS times each ---
    adapters = {name: _make_adapter(name) for name in ENGINES}
    for adapter in adapters.values():
        adapter.insert_batch(facts)

    result["query"] = {}
    for qclass in QUERY_CLASSES:
        query = _query_for_class(qclass, limit=num_facts * 10 + 10)
        canonical_by_engine: dict[str, list[dict[str, Any]]] = {}
        counts: dict[str, int] = {}
        stats: dict[str, dict[str, float]] = {}

        for engine_name, adapter in adapters.items():
            for _ in range(WARM_UP):
                adapter.execute_query(query)
            latencies = []
            last_facts: list[Any] = []
            for _ in range(NUM_RUNS):
                with MeasuredRun(label=f"{engine_name}_{qclass}") as mr:
                    last_facts = adapter.execute_query(query)
                latencies.append(mr.metrics().latency_ms)
            stats[engine_name] = compute_statistics(latencies).to_dict()
            counts[engine_name] = len(last_facts)
            canonical_by_engine[engine_name] = [_canonical_fact(f) for f in last_facts]

        v = verify_equivalence(canonical_by_engine)
        status = "OK" if v.passed else f"FAILED: {v.message}"
        print(f"    {qclass}: counts={counts} [{status}]")
        result["query"][qclass] = {
            "verified": v.passed,
            "verification_message": v.message,
            "result_counts": counts,
            "stats": stats,
        }

    return result


def main() -> int:
    results: dict[str, Any] = {
        "num_runs": NUM_RUNS,
        "warm_up": WARM_UP,
        "seed": 42,
        "lookup_anchor": LOOKUP_ANCHOR,
        "context_anchor": CONTEXT_ANCHOR,
        "scales": {},
    }
    for n_univ in UNIVERSITY_SCALES:
        print(f"Running LUBM benchmark at {n_univ} universities...")
        scale_result = run_scale(n_univ)
        results["scales"][str(scale_result["num_facts"])] = scale_result

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"Wrote {OUTPUT_PATH}")

    all_verified = all(
        entry["verified"]
        for scale in results["scales"].values()
        for entry in scale["query"].values()
    )
    if not all_verified:
        print(
            "WARNING: at least one query class failed cross-engine verification.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
