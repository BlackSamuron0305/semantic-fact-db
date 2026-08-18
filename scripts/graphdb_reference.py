#!/usr/bin/env python3
"""External reference benchmark: real Ontotext GraphDB vs SFDB.

Runs the paper's five query classes (LOOKUP, GLOBAL, CONTEXT, bounded
TEMPORAL, unbounded TEMPORAL) against a real, disk-backed Ontotext
GraphDB (free edition) store and against SFDB, on identical fact
streams. This is a third production-RDF-store comparison, alongside
scripts/jena_reference.py and scripts/virtuoso_reference.py, so the
crossover finding reported in paper/sections/evaluation.tex ("SFDB wins
LOOKUP/GLOBAL, a real optimiser wins CONTEXT/TEMPORAL at scale") rests
on three independently engineered optimisers rather than two.

Unlike scripts/rdflib_reference.py (a pure-Python, in-memory library,
not a production storage engine), GraphDB is a genuine external Java
process with its own disk-backed storage, query optimiser, and HTTP
server, developed independently of this project, Apache Jena, and
Virtuoso. Result counts are checked for agreement on every class at
every scale. Writes results/graphdb_reference.json, which
scripts/generate_tables.py turns into paper/tables/graphdb_reference.tex.

Requires a running GraphDB instance. The simplest route is the official
Docker image:

    docker run -d --name graphdb-sfdb -p 7200:7200 \\
        ontotext/graphdb:10.7.3

Unlike Virtuoso, GraphDB's free edition needs no authentication and no
explicit named graph for inserts; GraphDBEngineAdapter auto-creates the
"sfdb" repository on first use via GraphDB's REST API if it does not
already exist, so no manual setup step beyond starting the container is
required. See docs/benchmarking.md for details.

Usage: uv run python scripts/graphdb_reference.py [--base-url URL]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from common.interfaces import Query, QueryType
from common.types import Identifier
from sfdb.benchmark.engine_adapter import GraphDBEngineAdapter, SheafEngineAdapter
from sfdb.benchmark.paper_suite import (
    ANCHOR_ENTITY,
    CONTEXT_QUERY_ANCHOR,
    PAPER_SCALES,
    TEMPORAL_QUERY_END,
    TEMPORAL_QUERY_START,
    TEMPORAL_UNBOUNDED_QUERY_START,
)
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "results" / "graphdb_reference.json"

NUM_RUNS = 10
WARM_UP = 2

# Identical semantics and predicates to scripts/rdflib_reference.py's,
# scripts/jena_reference.py's, and scripts/virtuoso_reference.py's
# SPARQL_QUERIES — duplicated rather than cross-imported (scripts/ has
# no __init__.py, so `import scripts.foo` is not reliably importable
# depending on invocation directory). Keep all four in sync by hand;
# each is thin enough that drift would be obvious on review.
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


def run_scale(
    num_facts: int, graphdb: GraphDBEngineAdapter
) -> dict[str, dict[str, float | int | bool]]:
    config = SyntheticConfig(num_facts=num_facts, num_entities=max(20, num_facts // 10), seed=42)
    facts = list(generate_facts(config).facts)

    sfdb = SheafEngineAdapter()
    sfdb.insert_batch(facts)

    graphdb.clear()
    t0 = time.perf_counter()
    graphdb.insert_batch(facts)
    insert_s = time.perf_counter() - t0
    print(f"  N={num_facts}: GraphDB insert took {insert_s:.2f}s")

    out: dict[str, dict[str, float | int | bool]] = {"_insert_seconds": insert_s}  # type: ignore[dict-item]
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
            graphdb.execute_query_str(sparql)
        graphdb_lat: list[float] = []
        graphdb_count = 0
        for _ in range(NUM_RUNS):
            t0 = time.perf_counter()
            bindings = graphdb.execute_query_str(sparql)
            graphdb_lat.append((time.perf_counter() - t0) * 1000)
            graphdb_count = len(bindings)

        entry: dict[str, float | int | bool] = {
            "graphdb_mean_ms": statistics.fmean(graphdb_lat),
            "graphdb_stdev_ms": statistics.stdev(graphdb_lat) if len(graphdb_lat) > 1 else 0.0,
            "sfdb_mean_ms": statistics.fmean(sfdb_lat),
            "sfdb_stdev_ms": statistics.stdev(sfdb_lat) if len(sfdb_lat) > 1 else 0.0,
            "graphdb_count": graphdb_count,
            "sfdb_count": sfdb_count,
            "counts_match": graphdb_count == sfdb_count,
        }
        out[qclass] = entry
        status = "OK" if entry["counts_match"] else "COUNT MISMATCH"
        print(
            f"    {qclass}: GraphDB={entry['graphdb_mean_ms']:.3f}ms "
            f"({graphdb_count} rows), SFDB={entry['sfdb_mean_ms']:.3f}ms "
            f"({sfdb_count} rows) [{status}]"
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:7200")
    parser.add_argument(
        "--scales",
        type=int,
        nargs="+",
        default=list(PAPER_SCALES),
        help="Fact-count scales to run (default: the paper's four scales).",
    )
    args = parser.parse_args()

    graphdb = GraphDBEngineAdapter(base_url=args.base_url)
    if not graphdb._available:
        print(
            f"GraphDB not reachable at {args.base_url}. Start a GraphDB instance "
            "first — see docs/benchmarking.md.",
            file=sys.stderr,
        )
        return 1

    results: dict[str, object] = {
        "num_runs": NUM_RUNS,
        "warm_up": WARM_UP,
        "seed": 42,
        "base_url": args.base_url,
        "scales": {},
    }
    for n in args.scales:
        print(f"Running GraphDB reference at N={n}...")
        scales = results["scales"]
        assert isinstance(scales, dict)
        scales[str(n)] = run_scale(n, graphdb)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"Wrote {OUTPUT_PATH}")

    final_scales = results["scales"]
    assert isinstance(final_scales, dict)
    all_match = all(
        entry["counts_match"]
        for scale in final_scales.values()
        for qclass, entry in scale.items()
        if qclass != "_insert_seconds"
    )
    if not all_match:
        print("WARNING: at least one class/scale had a result-count mismatch.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
