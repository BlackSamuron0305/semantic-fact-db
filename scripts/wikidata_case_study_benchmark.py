#!/usr/bin/env python3
"""Real-world case study: benchmark the paper's five query classes against
a genuine, organic dataset instead of this project's own synthetic
generator.

Domain: national head-of-state/government office-holders sourced from
Wikidata (sfdb.datasets.wikidata_case_study) --- see
scripts/fetch_wikidata_case_study.py for how the snapshot was built.
Each fact is a real "position held" statement: WHO held WHAT office,
in WHICH country, WHEN --- exactly the n-ary, context-scoped,
temporally-qualified shape this paper's synthetic generator was built
to imitate, except this time the data was not constructed by this
project's authors to fit the design.

Runs the same three in-house engines (KnowledgeGraph, KnowledgeGraphMem,
SheafDatabase) and the same LOOKUP/GLOBAL/CONTEXT/TEMPORAL query
taxonomy as sfdb.benchmark.paper_suite, with the same three-way
cross-engine canonical-result verification, on a single fixed dataset
(there is only one real dataset here, not four synthetic scales).
Writes results/wikidata_case_study.json, which
scripts/generate_tables.py turns into
paper/tables/wikidata_case_study.tex.

Usage: uv run python scripts/wikidata_case_study_benchmark.py
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
from sfdb.datasets.wikidata_case_study import load_facts

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "results" / "wikidata_case_study.json"

NUM_RUNS = 10
WARM_UP = 2
ENGINES: tuple[str, ...] = ("KnowledgeGraph", "KnowledgeGraphMem", "SheafDatabase")
QUERY_CLASSES: tuple[str, ...] = ("LOOKUP", "GLOBAL", "CONTEXT", "TEMPORAL", "TEMPORAL_UNBOUNDED")

# Anchors chosen from the fetched snapshot itself (see the comment above
# each constant), the same way paper_suite.py's ANCHOR_ENTITY/
# CONTEXT_QUERY_ANCHOR/TEMPORAL_QUERY_START are fixed, documented
# constants rather than re-derived on every run -- picking anchors from
# live data on each run would make the query shape (and therefore the
# reported result count) silently depend on when the snapshot was last
# refreshed.
#
# LOOKUP_ANCHOR: the person who appears in the most facts in the
# snapshot -- Antonio Lopez de Santa Anna (Q189145), President of
# Mexico across eleven non-consecutive terms between 1833 and 1855, a
# genuinely non-trivial multi-row LOOKUP result of exactly the
# fragmented, repeated-office-holding shape real historical data
# produces and a synthetic generator would not naturally construct.
LOOKUP_ANCHOR = "http://www.wikidata.org/entity/Q189145"
# CONTEXT_ANCHOR: the country with the most recorded facts in the
# snapshot (Greece, 195 of 5,337 facts -- a long and fragmented 19th-
# and 20th-century political history, well represented since Wikidata
# editors have documented it thoroughly).
CONTEXT_ANCHOR = "world.Greece"
# A bounded window chosen to intersect a substantial fraction of the
# dated facts (92.6% of facts in the snapshot have a start date, 89.0%
# an end date; 1,047 of 5,337 facts have a start date inside this
# specific window).
TEMPORAL_QUERY_START = "1990-01-01T00:00:00+00:00"
TEMPORAL_QUERY_END = "2010-01-01T00:00:00+00:00"
TEMPORAL_UNBOUNDED_QUERY_START = "2000-01-01T00:00:00+00:00"


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


def main() -> int:
    facts = load_facts()
    num_facts = len(facts)
    print(f"Loaded {num_facts} real Wikidata facts.")

    results: dict[str, Any] = {
        "num_facts": num_facts,
        "num_runs": NUM_RUNS,
        "warm_up": WARM_UP,
        "lookup_anchor": LOOKUP_ANCHOR,
        "context_anchor": CONTEXT_ANCHOR,
        "insert": {},
        "query": {},
    }

    # --- Insert throughput: independent fresh-engine bulk inserts ---
    for engine_name in ENGINES:
        latencies = []
        for run_idx in range(NUM_RUNS):
            adapter = _make_adapter(engine_name)
            with MeasuredRun(label=f"{engine_name}_insert_{run_idx}") as mr:
                adapter.insert_batch(facts)
            latencies.append(mr.metrics().latency_ms)
        results["insert"][engine_name] = compute_statistics(latencies).to_dict()
        print(f"  insert {engine_name}: mean={results['insert'][engine_name]['mean']:.3f}ms")

    # --- Query classes: dataset populated once, queried NUM_RUNS times each ---
    adapters = {name: _make_adapter(name) for name in ENGINES}
    for adapter in adapters.values():
        adapter.insert_batch(facts)

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
        print(f"  {qclass}: counts={counts} [{status}]")
        results["query"][qclass] = {
            "verified": v.passed,
            "verification_message": v.message,
            "result_counts": counts,
            "stats": stats,
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"Wrote {OUTPUT_PATH}")

    all_verified = all(v["verified"] for v in results["query"].values())
    if not all_verified:
        print(
            "WARNING: at least one query class failed cross-engine verification.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
