"""Correctness tests for GraphDBEngineAdapter.

These tests require a running Ontotext GraphDB instance (see
paper/sections/artifact.tex or docs/benchmarking.md for the Docker
setup). They are skipped, not failed, when no such instance is
reachable, since CI environments and most local dev setups do not have
Docker/GraphDB running — this adapter exercises a genuine external
system, not code this repository controls.
"""

from __future__ import annotations

import pytest

from common.schema import SemanticFact
from sfdb.benchmark.engine_adapter import GraphDBEngineAdapter, RdflibEngineAdapter
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts

N_FACTS = 300


@pytest.fixture
def graphdb() -> GraphDBEngineAdapter:
    adapter = GraphDBEngineAdapter()
    if not adapter._available:
        pytest.skip("No GraphDB instance reachable at http://localhost:7200")
    adapter.clear()
    return adapter


@pytest.fixture(scope="module")
def facts() -> list[SemanticFact]:
    config = SyntheticConfig(num_facts=N_FACTS, num_entities=max(20, N_FACTS // 10), seed=42)
    return list(generate_facts(config).facts)


class TestGraphDBAdapterCorrectness:
    def test_insert_and_count(
        self, graphdb: GraphDBEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        graphdb.insert_batch(facts)
        result = graphdb.execute_query_str(
            "SELECT (COUNT(*) AS ?c) WHERE { ?s <ex:factId> ?id }"
        )
        assert result
        assert int(result[0]["c"]) == N_FACTS

    def test_lookup_matches_rdflib(
        self, graphdb: GraphDBEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        graphdb.insert_batch(facts)
        rdf = RdflibEngineAdapter()
        rdf.insert_batch(facts)

        sparql = 'SELECT ?event WHERE { ?event <ex:subject> "entity_0" . }'
        graphdb_result = graphdb.execute_query_str(sparql)
        rdf_result = rdf.execute_query_str(sparql)

        assert len(graphdb_result) == len(rdf_result)
        assert len(graphdb_result) > 0, "empty result makes this test vacuous"

    def test_clear_removes_all_triples(
        self, graphdb: GraphDBEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        graphdb.insert_batch(facts)
        graphdb.clear()
        result = graphdb.execute_query_str("SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
        assert int(result[0]["c"]) == 0

    def test_literal_escaping_survives_special_characters(
        self, graphdb: GraphDBEngineAdapter
    ) -> None:
        from common.schema import SemanticFact
        from common.types import Context, Identifier, Value

        tricky = SemanticFact(
            id=Identifier("f_special"),
            subject=Identifier('quote"backslash\\newline\ntab\t'),
            relation=Identifier("rel"),
            objects=(Value.literal("val"),),
            context=Context("world"),
        )
        graphdb.insert_batch([tricky])
        result = graphdb.execute_query_str("SELECT ?s WHERE { ?e <ex:factId> ?s }")
        assert result and result[0]["s"] == "f_special"

    def test_temporal_filter_matches_sfdb_semantics(
        self, graphdb: GraphDBEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        """GraphDB correctly filters plain (untyped) literal comparisons
        (unlike Virtuoso -- see test_virtuoso_adapter.py's equivalent
        regression test), but the shared query text uses STR(...) for all
        three production-store comparisons regardless, so this pins that
        GraphDB continues to agree with the portable form."""
        graphdb.insert_batch(facts)
        filtered = graphdb.execute_query_str(
            "SELECT ?event WHERE { ?event <ex:temporalStart> ?start . "
            'FILTER (STR(?start) < "2023-01-01T00:00:00+00:00") }'
        )
        unfiltered = graphdb.execute_query_str(
            "SELECT ?event WHERE { ?event <ex:temporalStart> ?start . }"
        )
        assert 0 < len(filtered) < len(unfiltered)
