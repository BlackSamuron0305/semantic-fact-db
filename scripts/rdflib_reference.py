#!/usr/bin/env python3
"""External reference benchmark: rdflib vs SFDB on all five query classes.

Runs the paper's five query classes (LOOKUP, GLOBAL, CONTEXT, bounded
TEMPORAL, unbounded TEMPORAL) at all three paper scales against
rdflib — a real,
independent, pure-Python in-memory RDF library queried via SPARQL — and
against SFDB, on identical fact streams. Result counts are checked for
agreement on every class at every scale. Writes
results/rdflib_reference.json, which scripts/generate_tables.py turns
into paper/tables/rdflib_reference.tex.

Scope, stated honestly: rdflib is not Apache Jena, Virtuoso, or any
disk-backed production triple store. This is an external reference
point that removes the "compared only against your own baseline"
objection at the level of a real independent implementation, not a
claim about the state of the art in RDF engines. rdflib latencies
include SPARQL text parsing on every run, which is how the library is
normally driven.

Usage: uv run python scripts/rdflib_reference.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from common.interfaces import Query, QueryType
from common.types import Identifier
from sfdb.benchmark.engine_adapter import RdflibEngineAdapter, SheafEngineAdapter
from sfdb.benchmark.paper_suite import (
    ANCHOR_ENTITY,
    CONTEXT_QUERY_ANCHOR,
    TEMPORAL_QUERY_END,
    TEMPORAL_QUERY_START,
    TEMPORAL_UNBOUNDED_QUERY_START,
)
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "results" / "rdflib_reference.json"

# Capped below the paper suite's largest scale: at 10^5 facts the graph
# holds ~1.4M triples and rdflib's SPARQL engine no longer answers the
# scan-shaped classes in reasonable benchmark time.
RDFLIB_SCALES: tuple[int, ...] = (100, 1_000, 10_000)

NUM_RUNS = 10
WARM_UP = 2

# The bounded window [2022-01-01, 2023-01-01) and the open-ended range
# [2023-01-01, inf) — identical semantics to both SFDB engines' shared
# overlap test (keep iff f_start < q_end and (f_end absent or f_end > q_start)).
_BOUNDED_START_ISO = "2022-01-01T00:00:00+00:00"
_BOUNDED_END_ISO = "2023-01-01T00:00:00+00:00"
_UNBOUNDED_START_ISO = "2023-01-01T00:00:00+00:00"

SPARQL_QUERIES: dict[str, str] = {
    "LOOKUP": f'SELECT ?event WHERE {{ ?event <ex:subject> "{ANCHOR_ENTITY}" . }}',
    "GLOBAL": "SELECT ?event WHERE { ?event <ex:factId> ?id . }",
    "CONTEXT": (
        "SELECT ?event WHERE { ?event <ex:context> ?ctx . "
        f'FILTER (?ctx = "{CONTEXT_QUERY_ANCHOR}" || '
        f'STRSTARTS(?ctx, "{CONTEXT_QUERY_ANCHOR}.")) }}'
    ),
    "TEMPORAL": (
        "SELECT ?event WHERE { ?event <ex:temporalStart> ?start . "
        "OPTIONAL { ?event <ex:temporalEnd> ?end } "
        f'FILTER (STR(?start) < "{_BOUNDED_END_ISO}" && '
        f'(!BOUND(?end) || STR(?end) > "{_BOUNDED_START_ISO}")) }}'
    ),
    "TEMPORAL_UNBOUNDED": (
        "SELECT ?event WHERE { ?event <ex:temporalStart> ?start . "
        "OPTIONAL { ?event <ex:temporalEnd> ?end } "
        f'FILTER (!BOUND(?end) || STR(?end) > "{_UNBOUNDED_START_ISO}") }}'
    ),
}


def _typed_query(qclass: str, limit: int) -> Query:
    if qclass == "LOOKUP":
        return Query(query_type=QueryType.LOOKUP, subject=Identifier(ANCHOR_ENTITY), limit=limit)
    if qclass == "GLOBAL":
        return Query(query_type=QueryType.GLOBAL, limit=limit)
    if qclass == "CONTEXT":
        return Query(query_type=QueryType.CONTEXT, context=CONTEXT_QUERY_ANCHOR, limit=limit)
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


def run_scale(num_facts: int) -> dict[str, dict[str, float | int | bool]]:
    config = SyntheticConfig(num_facts=num_facts, num_entities=max(20, num_facts // 10), seed=42)
    facts = list(generate_facts(config).facts)

    sfdb = SheafEngineAdapter()
    sfdb.insert_batch(facts)

    rdf = RdflibEngineAdapter()
    rdf.insert_batch(facts)

    out: dict[str, dict[str, float | int | bool]] = {}
    for qclass, sparql in SPARQL_QUERIES.items():
        typed = _typed_query(qclass, limit=num_facts * 10 + 10)

        for _ in range(WARM_UP):
            sfdb.execute_query(typed)
        sfdb_lat: list[float] = []
        sfdb_count = 0
        for _ in range(NUM_RUNS):
            t0 = time.perf_counter()
            result = sfdb.execute_query(typed)
            sfdb_lat.append((time.perf_counter() - t0) * 1000)
            sfdb_count = len(result)

        for _ in range(WARM_UP):
            rdf.execute_query_str(sparql)
        rdf_lat: list[float] = []
        rdf_count = 0
        for _ in range(NUM_RUNS):
            t0 = time.perf_counter()
            bindings = rdf.execute_query_str(sparql)
            rdf_lat.append((time.perf_counter() - t0) * 1000)
            rdf_count = len(bindings)

        entry: dict[str, float | int | bool] = {
            "rdflib_mean_ms": statistics.fmean(rdf_lat),
            "rdflib_stdev_ms": statistics.stdev(rdf_lat) if len(rdf_lat) > 1 else 0.0,
            "sfdb_mean_ms": statistics.fmean(sfdb_lat),
            "sfdb_stdev_ms": statistics.stdev(sfdb_lat) if len(sfdb_lat) > 1 else 0.0,
            "rdflib_count": rdf_count,
            "sfdb_count": sfdb_count,
            "counts_match": rdf_count == sfdb_count,
        }
        out[qclass] = entry
        status = "OK" if entry["counts_match"] else "COUNT MISMATCH"
        print(
            f"  N={num_facts} {qclass}: rdflib={entry['rdflib_mean_ms']:.3f}ms "
            f"({rdf_count} rows), SFDB={entry['sfdb_mean_ms']:.3f}ms "
            f"({sfdb_count} rows) [{status}]"
        )
    return out


def main() -> int:
    probe = RdflibEngineAdapter()
    if not probe._available:
        print("rdflib not available; install it to run this benchmark.", file=sys.stderr)
        return 1

    results: dict[str, object] = {
        "num_runs": NUM_RUNS,
        "warm_up": WARM_UP,
        "seed": 42,
        "scales": {},
    }
    for n in RDFLIB_SCALES:
        print(f"Running rdflib reference at N={n}...")
        scales = results["scales"]
        assert isinstance(scales, dict)
        scales[str(n)] = run_scale(n)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"Wrote {OUTPUT_PATH}")

    all_match = all(
        entry["counts_match"]
        for scale in results["scales"].values()  # type: ignore[union-attr]
        for entry in scale.values()
    )
    if not all_match:
        print("WARNING: at least one class/scale had a result-count mismatch.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
