#!/usr/bin/env python3
"""A small, honest external-baseline spot-check against rdflib.

This is NOT a comparison against Apache Jena, GraphDB, or any other
production RDF store with its own storage engine -- it measures rdflib
(a pure-Python, in-memory RDF library), which is what
sfdb.benchmark.engine_adapter.JenaEngineAdapter actually wraps despite its
name. That is the honest scope of this script: a single query class, a
single scale, against a real (if lightweight) independent RDF
implementation, not our own KG baseline. A full comparison against a
production triple store with its own storage engine remains future work
(see paper/sections/future_work.tex).

Usage: uv run python scripts/rdflib_spotcheck.py
"""

from __future__ import annotations

import time

from common.interfaces import Query, QueryType
from common.types import Identifier
from sfdb.benchmark.engine_adapter import JenaEngineAdapter, SheafEngineAdapter
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts

N = 1000
ANCHOR = "entity_0"
NUM_RUNS = 10
WARM_UP = 2


def main() -> None:
    config = SyntheticConfig(num_facts=N, num_entities=max(20, N // 10), seed=42)
    dataset = generate_facts(config)
    facts = dataset.facts

    sfdb = SheafEngineAdapter()
    sfdb.insert_batch(facts)

    rdf = JenaEngineAdapter()
    if not rdf._available:
        print("rdflib not available; install it to run this spot-check.")
        return
    rdf.insert_batch(facts)

    q = Query(query_type=QueryType.LOOKUP, subject=Identifier(ANCHOR), limit=N * 10 + 10)
    for _ in range(WARM_UP):
        sfdb.execute_query(q)
    sfdb_lat = []
    for _ in range(NUM_RUNS):
        t0 = time.perf_counter()
        sfdb_result = sfdb.execute_query(q)
        sfdb_lat.append((time.perf_counter() - t0) * 1000)

    sparql = f'SELECT ?event WHERE {{ ?event <ex:subject> "{ANCHOR}" . }}'
    for _ in range(WARM_UP):
        rdf.execute_query_str(sparql)
    rdf_lat = []
    for _ in range(NUM_RUNS):
        t0 = time.perf_counter()
        rdf_result = rdf.execute_query_str(sparql)
        rdf_lat.append((time.perf_counter() - t0) * 1000)

    sfdb_mean = sum(sfdb_lat) / len(sfdb_lat)
    rdf_mean = sum(rdf_lat) / len(rdf_lat)
    print(f"N={N} facts, LOOKUP query on anchor entity {ANCHOR!r}")
    print(f"  SFDB:   mean={sfdb_mean:.4f}ms over {NUM_RUNS} runs, {len(sfdb_result)} results")
    print(f"  rdflib: mean={rdf_mean:.4f}ms over {NUM_RUNS} runs, {len(rdf_result)} results")
    print(f"  ratio (rdflib / SFDB): {rdf_mean / sfdb_mean:.2f}x")
    if len(sfdb_result) != len(rdf_result):
        print("  WARNING: result counts differ -- not a like-for-like comparison.")


if __name__ == "__main__":
    main()
