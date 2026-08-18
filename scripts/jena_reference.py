#!/usr/bin/env python3
"""External reference benchmark: real Apache Jena TDB2 vs SFDB.

Runs the paper's five query classes (LOOKUP, GLOBAL, CONTEXT, bounded
TEMPORAL, unbounded TEMPORAL) against a real, disk-backed Apache Jena
TDB2 store (via a running Fuseki HTTP server) and against SFDB, on
identical fact streams. This is the production-RDF-store comparison
every reviewer persona in research/reviewer_simulation.md named as the
single highest-leverage gap in the evaluation, and what
paper/sections/future_work.tex previously scoped out entirely.

Unlike scripts/rdflib_reference.py (a pure-Python, in-memory library
written by the same open-source community this project draws on, but
not a production storage engine), Jena TDB2 is a genuine external Java
process with its own disk-backed B+tree storage, query optimiser, and
HTTP server, developed independently of this project. Result counts are
checked for agreement on every class at every scale. Writes
results/jena_reference.json, which scripts/generate_tables.py turns into
paper/tables/jena_reference.tex.

Requires a running Fuseki server with a TDB2-backed dataset. See
docs/benchmarking.md for setup instructions. Example (from a Jena Fuseki
distribution directory):

    java -jar fuseki-server.jar --loc=<TDB2_DIR> --update --port 3030 /sfdb

Usage: uv run python scripts/jena_reference.py [--base-url URL]
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
from sfdb.benchmark.engine_adapter import JenaTDB2EngineAdapter, SheafEngineAdapter
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
OUTPUT_PATH = REPO_ROOT / "results" / "jena_reference.json"

NUM_RUNS = 10
WARM_UP = 2

# Identical semantics and predicates to scripts/rdflib_reference.py's
# SPARQL_QUERIES — duplicated rather than cross-imported (scripts/ has
# no __init__.py, so `import scripts.rdflib_reference` is not reliably
# importable depending on invocation directory). Keep the two in sync by
# hand; both are thin enough that drift would be obvious on review.
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
    num_facts: int, jena: JenaTDB2EngineAdapter
) -> dict[str, dict[str, float | int | bool]]:
    config = SyntheticConfig(num_facts=num_facts, num_entities=max(20, num_facts // 10), seed=42)
    facts = list(generate_facts(config).facts)

    sfdb = SheafEngineAdapter()
    sfdb.insert_batch(facts)

    jena.clear()
    t0 = time.perf_counter()
    jena.insert_batch(facts)
    insert_s = time.perf_counter() - t0
    print(f"  N={num_facts}: Jena insert took {insert_s:.2f}s")

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
            jena.execute_query_str(sparql)
        jena_lat: list[float] = []
        jena_count = 0
        for _ in range(NUM_RUNS):
            t0 = time.perf_counter()
            bindings = jena.execute_query_str(sparql)
            jena_lat.append((time.perf_counter() - t0) * 1000)
            jena_count = len(bindings)

        entry: dict[str, float | int | bool] = {
            "jena_mean_ms": statistics.fmean(jena_lat),
            "jena_stdev_ms": statistics.stdev(jena_lat) if len(jena_lat) > 1 else 0.0,
            "sfdb_mean_ms": statistics.fmean(sfdb_lat),
            "sfdb_stdev_ms": statistics.stdev(sfdb_lat) if len(sfdb_lat) > 1 else 0.0,
            "jena_count": jena_count,
            "sfdb_count": sfdb_count,
            "counts_match": jena_count == sfdb_count,
        }
        out[qclass] = entry
        status = "OK" if entry["counts_match"] else "COUNT MISMATCH"
        print(
            f"    {qclass}: Jena={entry['jena_mean_ms']:.3f}ms "
            f"({jena_count} rows), SFDB={entry['sfdb_mean_ms']:.3f}ms "
            f"({sfdb_count} rows) [{status}]"
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:3030/sfdb")
    parser.add_argument(
        "--scales",
        type=int,
        nargs="+",
        default=list(PAPER_SCALES),
        help="Fact-count scales to run (default: the paper's four scales).",
    )
    args = parser.parse_args()

    jena = JenaTDB2EngineAdapter(base_url=args.base_url)
    if not jena._available:
        print(
            f"Jena/Fuseki not reachable at {args.base_url}. Start a Fuseki server with a "
            "TDB2 dataset first — see docs/benchmarking.md.",
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
        print(f"Running Jena TDB2 reference at N={n}...")
        scales = results["scales"]
        assert isinstance(scales, dict)
        scales[str(n)] = run_scale(n, jena)

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
