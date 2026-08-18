"""Correctness tests for VirtuosoEngineAdapter.

These tests require a running OpenLink Virtuoso instance (see
paper/sections/artifact.tex or docs/benchmarking.md for the Docker
setup). They are skipped, not failed, when no such instance is
reachable, since CI environments and most local dev setups do not have
Docker/Virtuoso running — this adapter exercises a genuine external
system, not code this repository controls.
"""

from __future__ import annotations

import pytest

from common.schema import SemanticFact
from sfdb.benchmark.engine_adapter import RdflibEngineAdapter, VirtuosoEngineAdapter
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts

N_FACTS = 300


@pytest.fixture
def virtuoso() -> VirtuosoEngineAdapter:
    adapter = VirtuosoEngineAdapter()
    if not adapter._available:
        pytest.skip("No Virtuoso instance reachable at http://localhost:8890")
    adapter.clear()
    return adapter


@pytest.fixture(scope="module")
def facts() -> list[SemanticFact]:
    config = SyntheticConfig(num_facts=N_FACTS, num_entities=max(20, N_FACTS // 10), seed=42)
    return list(generate_facts(config).facts)


class TestVirtuosoAdapterCorrectness:
    def test_insert_and_count(
        self, virtuoso: VirtuosoEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        virtuoso.insert_batch(facts)
        result = virtuoso.execute_query_str(
            "SELECT (COUNT(*) AS ?c) WHERE { ?s <ex:factId> ?id }"
        )
        assert result
        assert int(result[0]["c"]) == N_FACTS

    def test_lookup_matches_rdflib(
        self, virtuoso: VirtuosoEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        virtuoso.insert_batch(facts)
        rdf = RdflibEngineAdapter()
        rdf.insert_batch(facts)

        sparql = 'SELECT ?event WHERE { ?event <ex:subject> "entity_0" . }'
        virtuoso_result = virtuoso.execute_query_str(sparql)
        rdf_result = rdf.execute_query_str(sparql)

        assert len(virtuoso_result) == len(rdf_result)
        assert len(virtuoso_result) > 0, "empty result makes this test vacuous"

    def test_clear_removes_all_triples(
        self, virtuoso: VirtuosoEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        virtuoso.insert_batch(facts)
        virtuoso.clear()
        result = virtuoso.execute_query_str("SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
        assert int(result[0]["c"]) == 0

    def test_literal_escaping_survives_special_characters(
        self, virtuoso: VirtuosoEngineAdapter
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
        virtuoso.insert_batch([tricky])
        result = virtuoso.execute_query_str("SELECT ?s WHERE { ?e <ex:factId> ?s }")
        assert result and result[0]["s"] == "f_special"

    def test_temporal_filter_matches_sfdb_semantics(
        self, virtuoso: VirtuosoEngineAdapter, facts: list[SemanticFact]
    ) -> None:
        """Regression test for the STR() coercion fix.

        Virtuoso's SPARQL engine does not filter plain (untyped) RDF
        literals with bare `<`/`>` the way Jena and rdflib do -- it
        silently returns every row unfiltered instead. The shared
        SPARQL_QUERIES text in scripts/{jena,rdflib,virtuoso}_reference.py
        wraps the compared variable in STR(...) to force an unambiguous
        string comparison that all three engines agree on; this pins that
        fix against regressing back to the unfiltered behaviour.
        """
        virtuoso.insert_batch(facts)
        unfiltered = virtuoso.execute_query_str(
            "SELECT ?event WHERE { ?event <ex:temporalStart> ?start . }"
        )
        filtered = virtuoso.execute_query_str(
            "SELECT ?event WHERE { ?event <ex:temporalStart> ?start . "
            'FILTER (STR(?start) < "2023-01-01T00:00:00+00:00") }'
        )
        assert 0 < len(filtered) < len(unfiltered)
