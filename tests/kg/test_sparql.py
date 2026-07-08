"""Tests for the SPARQL parser and executor."""

from __future__ import annotations

import pytest

from common.exceptions import QueryError
from sfdb.kg.engine import KnowledgeGraphEngine
from sfdb.kg.sparql import (
    SparqlQuery,
    parse_sparql,
)


@pytest.fixture
def engine() -> KnowledgeGraphEngine:
    eng = KnowledgeGraphEngine()
    eng.create()
    return eng


class TestSparqlParser:
    def test_parse_simple(self) -> None:
        query_str = "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"
        result = parse_sparql(query_str)
        assert isinstance(result, SparqlQuery)
        assert result.select_vars == ("?s", "?p", "?o")
        assert len(result.patterns) == 1
        assert result.patterns[0].subject == "?s"
        assert result.patterns[0].predicate == "?p"
        assert result.patterns[0].obj == "?o"

    def test_parse_with_filters(self) -> None:
        query_str = 'SELECT ?s WHERE { ?s ?p ?o . FILTER(?o = "hello") }'
        result = parse_sparql(query_str)
        assert len(result.patterns) == 1
        assert len(result.filters) == 1

    def test_parse_with_limit(self) -> None:
        query_str = "SELECT ?s WHERE { ?s ?p ?o } LIMIT 10"
        result = parse_sparql(query_str)
        assert result.limit == 10

    def test_parse_with_order(self) -> None:
        query_str = "SELECT ?s WHERE { ?s ?p ?o } ORDER BY ?s"
        result = parse_sparql(query_str)
        assert result.order is not None
        assert result.order.variable == "?s"
        assert result.order.ascending is True

    def test_parse_invalid(self) -> None:
        with pytest.raises((ValueError, QueryError), match="Expected SELECT"):
            parse_sparql("BAD QUERY")

    def test_parse_triple_with_type(self) -> None:
        query_str = "SELECT ?s WHERE { ?s a ?o }"
        result = parse_sparql(query_str)
        assert len(result.patterns) == 1
        assert result.patterns[0].predicate == "a"

    def test_parse_with_offset(self) -> None:
        query_str = "SELECT ?s WHERE { ?s ?p ?o } OFFSET 5"
        result = parse_sparql(query_str)
        assert result.offset == 5


class TestSparqlExecutor:
    def test_execute_select_all(self, engine: KnowledgeGraphEngine) -> None:
        query_str = "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"
        results = engine.query_sparql(query_str)
        assert isinstance(results, list)

    def test_execute_with_data(self, engine: KnowledgeGraphEngine) -> None:
        query_str = "SELECT ?s WHERE { ?s ?p ?o }"
        results = engine.query_sparql(query_str)
        assert isinstance(results, list)

    def test_execute_invalid_query(self, engine: KnowledgeGraphEngine) -> None:
        results = engine.query_sparql("BAD")
        assert len(results) == 0
