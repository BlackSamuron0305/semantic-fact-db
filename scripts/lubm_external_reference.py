#!/usr/bin/env python3
"""LUBM data against a real external production store (Jena, Virtuoso, or GraphDB).

Combines the two extensions this paper's own future-work section named
as still open after scripts/lubm_benchmark.py: LUBM data has been run
against this project's own three in-house engines, and each of Jena,
Virtuoso, and GraphDB has been run against this project's own synthetic
generator, but neither axis had been varied together. This script runs
LUBM (Lehigh University Benchmark) data against a real, disk-backed
external production store, over the identical SPARQL query text and
LUBM-specific anchors used in scripts/lubm_benchmark.py, at the same
four university-count scales.

If SFDB's LOOKUP/GLOBAL/CONTEXT advantage and TEMPORAL crossover
(Sections eval:jena/virtuoso/graphdb, all measured on the synthetic
generator) are properties of the design and the query shapes rather
than of the synthetic generator's specific topology, they should
reproduce here too, where both the dataset and the comparison engine
are varied simultaneously. Writes
results/lubm_<store>_reference.json, which scripts/generate_tables.py
turns into paper/tables/lubm_<store>_reference.tex.

Usage: uv run python scripts/lubm_external_reference.py --store jena \
    (or --store virtuoso, --store graphdb) [--base-url URL]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from common.interfaces import Query, QueryType
from common.types import Identifier
from sfdb.benchmark.engine_adapter import (
    GraphDBEngineAdapter,
    JenaTDB2EngineAdapter,
    SheafEngineAdapter,
    VirtuosoEngineAdapter,
)
from sfdb.datasets.lubm import LUBMConfig, LUBMGenerator

REPO_ROOT = Path(__file__).resolve().parent.parent

STORES: dict[str, dict[str, Any]] = {
    "jena": {
        "adapter_cls": JenaTDB2EngineAdapter,
        "default_base_url": "http://localhost:3030/sfdb",
        "label": "Jena",
    },
    "virtuoso": {
        "adapter_cls": VirtuosoEngineAdapter,
        "default_base_url": "http://localhost:8890",
        "label": "Virtuoso",
    },
    "graphdb": {
        "adapter_cls": GraphDBEngineAdapter,
        "default_base_url": "http://localhost:7200",
        "label": "GraphDB",
    },
}

NUM_RUNS = 10
WARM_UP = 2

# Identical university-count scales and LUBM-specific anchors to
# scripts/lubm_benchmark.py -- see that module's comments for why these
# particular values were chosen.
UNIVERSITY_SCALES: tuple[int, ...] = (1, 3, 26, 265)
LOOKUP_ANCHOR = "http://www.FullProfessor0.Department0.University0"
CONTEXT_ANCHOR = "world.University0.dept0"
_BOUNDED_START_ISO = "2018-01-01T00:00:00+00:00"
_BOUNDED_END_ISO = "2020-01-01T00:00:00+00:00"
_UNBOUNDED_START_ISO = "2022-01-01T00:00:00+00:00"

# Identical shared-query-text pattern to scripts/{jena,virtuoso,graphdb}_reference.py,
# with LUBM's own anchors substituted for the synthetic generator's.
SPARQL_QUERIES: dict[str, str] = {
    "LOOKUP": f'SELECT ?event WHERE {{ ?event <ex:subject> "{LOOKUP_ANCHOR}" . }}',
    "GLOBAL": "SELECT ?event WHERE { ?event <ex:factId> ?id . }",
    "CONTEXT": (
        "SELECT ?event WHERE { ?event <ex:context> ?ctx . "
        f'FILTER (?ctx = "{CONTEXT_ANCHOR}" || '
        f'STRSTARTS(?ctx, "{CONTEXT_ANCHOR}.")) }}'
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
        return Query(query_type=QueryType.LOOKUP, subject=Identifier(LOOKUP_ANCHOR), limit=limit)
    if qclass == "GLOBAL":
        return Query(query_type=QueryType.GLOBAL, limit=limit)
    if qclass == "CONTEXT":
        return Query(query_type=QueryType.CONTEXT, context=CONTEXT_ANCHOR, limit=limit)
    if qclass == "TEMPORAL":
        return Query(
            query_type=QueryType.TEMPORAL,
            temporal_start=_BOUNDED_START_ISO,
            temporal_end=_BOUNDED_END_ISO,
            limit=limit,
        )
    if qclass == "TEMPORAL_UNBOUNDED":
        return Query(
            query_type=QueryType.TEMPORAL,
            temporal_start=_UNBOUNDED_START_ISO,
            temporal_end=None,
            limit=limit,
        )
    raise ValueError(f"Unknown query class: {qclass}")


def run_scale(num_universities: int, external: Any) -> dict[str, Any]:
    facts = LUBMGenerator(LUBMConfig(num_universities=num_universities, seed=42)).generate()
    num_facts = len(facts)
    print(f"  {num_universities} universities -> {num_facts} facts")

    sfdb = SheafEngineAdapter()
    sfdb.insert_batch(facts)

    external.clear()
    t0 = time.perf_counter()
    external.insert_batch(facts)
    insert_s = time.perf_counter() - t0
    print(f"    insert took {insert_s:.2f}s")

    out: dict[str, Any] = {"_insert_seconds": insert_s, "num_facts": num_facts}
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
            external.execute_query_str(sparql)
        ext_lat: list[float] = []
        ext_count = 0
        for _ in range(NUM_RUNS):
            t0 = time.perf_counter()
            bindings = external.execute_query_str(sparql)
            ext_lat.append((time.perf_counter() - t0) * 1000)
            ext_count = len(bindings)

        entry: dict[str, Any] = {
            "external_mean_ms": statistics.fmean(ext_lat),
            "external_stdev_ms": statistics.stdev(ext_lat) if len(ext_lat) > 1 else 0.0,
            "sfdb_mean_ms": statistics.fmean(sfdb_lat),
            "sfdb_stdev_ms": statistics.stdev(sfdb_lat) if len(sfdb_lat) > 1 else 0.0,
            "external_count": ext_count,
            "sfdb_count": sfdb_count,
            "counts_match": ext_count == sfdb_count,
        }
        out[qclass] = entry
        status = "OK" if entry["counts_match"] else "COUNT MISMATCH"
        print(
            f"    {qclass}: external={entry['external_mean_ms']:.3f}ms "
            f"({ext_count} rows), SFDB={entry['sfdb_mean_ms']:.3f}ms "
            f"({sfdb_count} rows) [{status}]"
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True, choices=sorted(STORES))
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    store = STORES[args.store]
    base_url = args.base_url or store["default_base_url"]
    external = store["adapter_cls"](base_url=base_url)
    if not external._available:
        print(
            f"{store['label']} not reachable at {base_url}. Start it first "
            "-- see docs/benchmarking.md.",
            file=sys.stderr,
        )
        return 1

    output_path = REPO_ROOT / "results" / f"lubm_{args.store}_reference.json"
    results: dict[str, Any] = {
        "store": args.store,
        "num_runs": NUM_RUNS,
        "warm_up": WARM_UP,
        "seed": 42,
        "base_url": base_url,
        "lookup_anchor": LOOKUP_ANCHOR,
        "context_anchor": CONTEXT_ANCHOR,
        "scales": {},
    }
    for n_univ in UNIVERSITY_SCALES:
        print(f"Running LUBM-vs-{store['label']} at {n_univ} universities...")
        scale_result = run_scale(n_univ, external)
        results["scales"][str(scale_result["num_facts"])] = scale_result

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote {output_path}")

    all_match = all(
        entry["counts_match"]
        for scale in results["scales"].values()
        for qclass, entry in scale.items()
        if qclass not in ("_insert_seconds", "num_facts")
    )
    if not all_match:
        print("WARNING: at least one class/scale had a result-count mismatch.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
