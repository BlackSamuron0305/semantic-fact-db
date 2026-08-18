"""Correctness tests for JenaTDB2EngineAdapter.

These tests require a running Fuseki server with a TDB2 dataset at
/sfdb (see paper/sections/artifact.tex or docs/benchmarking.md for
setup). They are skipped, not failed, when no such server is reachable,
since CI environments and most local dev setups do not have Java/Jena
installed — this adapter exercises a genuine external system, not code
this repository controls.
"""

from __future__ import annotations

import pytest

from common.schema import SemanticFact
from sfdb.benchmark.engine_adapter import JenaTDB2EngineAdapter, RdflibEngineAdapter
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts

N_FACTS = 300


@pytest.fixture
def jena() -> JenaTDB2EngineAdapter:
    adapter = JenaTDB2EngineAdapter()
    if not adapter._available:
        pytest.skip("No Fuseki/Jena TDB2 server reachable at http://localhost:3030/sfdb")
    adapter.clear()
    return adapter


@pytest.fixture(scope="module")
def facts() -> list[SemanticFact]:
    config = SyntheticConfig(num_facts=N_FACTS, num_entities=max(20, N_FACTS // 10), seed=42)
    return list(generate_facts(config).facts)


class TestJenaAdapterCorrectness:
    def test_insert_and_count(
        self, jena: JenaTDB2EngineAdapter, facts: list[SemanticFact]
    ) -> None:
        jena.insert_batch(facts)
        result = jena.execute_query_str("SELECT (COUNT(*) AS ?c) WHERE { ?s <ex:factId> ?id }")
        assert result
        assert int(result[0]["c"]) == N_FACTS

    def test_lookup_matches_rdflib(
        self, jena: JenaTDB2EngineAdapter, facts: list[SemanticFact]
    ) -> None:
        jena.insert_batch(facts)
        rdf = RdflibEngineAdapter()
        rdf.insert_batch(facts)

        sparql = 'SELECT ?event WHERE { ?event <ex:subject> "entity_0" . }'
        jena_result = jena.execute_query_str(sparql)
        rdf_result = rdf.execute_query_str(sparql)

        assert len(jena_result) == len(rdf_result)
        assert len(jena_result) > 0, "empty result makes this test vacuous"

    def test_clear_removes_all_triples(
        self, jena: JenaTDB2EngineAdapter, facts: list[SemanticFact]
    ) -> None:
        jena.insert_batch(facts)
        jena.clear()
        result = jena.execute_query_str("SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
        assert int(result[0]["c"]) == 0

    def test_literal_escaping_survives_special_characters(
        self, jena: JenaTDB2EngineAdapter
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
        jena.insert_batch([tricky])
        result = jena.execute_query_str("SELECT ?s WHERE { ?e <ex:factId> ?s }")
        assert result and result[0]["s"] == "f_special"
