#!/usr/bin/env python3
"""External reference benchmark: real OpenLink Virtuoso vs SFDB.

Runs the paper's five query classes (LOOKUP, GLOBAL, CONTEXT, bounded
TEMPORAL, unbounded TEMPORAL) against a real, disk-backed OpenLink
Virtuoso open-source store and against SFDB, on identical fact streams.
This is a second production-RDF-store comparison, alongside
scripts/jena_reference.py, so the crossover finding reported in
paper/sections/evaluation.tex ("SFDB wins LOOKUP/GLOBAL, a real
optimiser wins CONTEXT/TEMPORAL at scale") does not rest on one vendor's
query optimiser.

Unlike scripts/rdflib_reference.py (a pure-Python, in-memory library,
not a production storage engine), Virtuoso is a genuine external C
process with its own disk-backed column store, cost-based query
optimiser, and HTTP server, developed independently of this project and
of Apache Jena. Result counts are checked for agreement on every class
at every scale. Writes results/virtuoso_reference.json, which
scripts/generate_tables.py turns into paper/tables/virtuoso_reference.tex.

Requires a running Virtuoso instance. The simplest route is the official
Docker image:

    docker run -d --name virtuoso-sfdb -p 8890:8890 -p 1111:1111 \\
        -e DBA_PASSWORD=sfdb_bench_2026 \\
        openlink/virtuoso-opensource-7:latest

See docs/benchmarking.md for setup instructions and the Virtuoso-specific
quirks (HTTP Digest auth, named-graph inserts, SPARQL Update batch-size
limits) this adapter works around.

Usage: uv run python scripts/virtuoso_reference.py [--base-url URL]
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
from sfdb.benchmark.engine_adapter import SheafEngineAdapter, VirtuosoEngineAdapter
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
OUTPUT_PATH = REPO_ROOT / "results" / "virtuoso_reference.json"

NUM_RUNS = 10
WARM_UP = 2

# Identical semantics and predicates to scripts/rdflib_reference.py's and
# scripts/jena_reference.py's SPARQL_QUERIES — duplicated rather than
# cross-imported (scripts/ has no __init__.py, so `import scripts.foo` is
# not reliably importable depending on invocation directory). Keep all
# three in sync by hand; each is thin enough that drift would be obvious
# on review.
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
    num_facts: int, virtuoso: VirtuosoEngineAdapter
) -> dict[str, dict[str, float | int | bool]]:
    config = SyntheticConfig(num_facts=num_facts, num_entities=max(20, num_facts // 10), seed=42)
    facts = list(generate_facts(config).facts)

    sfdb = SheafEngineAdapter()
    sfdb.insert_batch(facts)

    virtuoso.clear()
    t0 = time.perf_counter()
    virtuoso.insert_batch(facts)
    insert_s = time.perf_counter() - t0
    print(f"  N={num_facts}: Virtuoso insert took {insert_s:.2f}s")

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
            virtuoso.execute_query_str(sparql)
        virtuoso_lat: list[float] = []
        virtuoso_count = 0
        for _ in range(NUM_RUNS):
            t0 = time.perf_counter()
            bindings = virtuoso.execute_query_str(sparql)
            virtuoso_lat.append((time.perf_counter() - t0) * 1000)
            virtuoso_count = len(bindings)

        entry: dict[str, float | int | bool] = {
            "virtuoso_mean_ms": statistics.fmean(virtuoso_lat),
            "virtuoso_stdev_ms": statistics.stdev(virtuoso_lat) if len(virtuoso_lat) > 1 else 0.0,
            "sfdb_mean_ms": statistics.fmean(sfdb_lat),
            "sfdb_stdev_ms": statistics.stdev(sfdb_lat) if len(sfdb_lat) > 1 else 0.0,
            "virtuoso_count": virtuoso_count,
            "sfdb_count": sfdb_count,
            "counts_match": virtuoso_count == sfdb_count,
        }
        out[qclass] = entry
        status = "OK" if entry["counts_match"] else "COUNT MISMATCH"
        print(
            f"    {qclass}: Virtuoso={entry['virtuoso_mean_ms']:.3f}ms "
            f"({virtuoso_count} rows), SFDB={entry['sfdb_mean_ms']:.3f}ms "
            f"({sfdb_count} rows) [{status}]"
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8890")
    parser.add_argument(
        "--scales",
        type=int,
        nargs="+",
        default=list(PAPER_SCALES),
        help="Fact-count scales to run (default: the paper's four scales).",
    )
    args = parser.parse_args()

    virtuoso = VirtuosoEngineAdapter(base_url=args.base_url)
    if not virtuoso._available:
        print(
            f"Virtuoso not reachable at {args.base_url}. Start a Virtuoso instance "
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
        print(f"Running Virtuoso reference at N={n}...")
        scales = results["scales"]
        assert isinstance(scales, dict)
        scales[str(n)] = run_scale(n, virtuoso)

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
