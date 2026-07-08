"""Adapter that maps unified Queries to KGQueryEngine calls.

This adapter enables the QueryEngine to dispatch unified queries
to the Knowledge Graph subsystem.

Complexity
----------
Adaptation: O(1) — direct mapping of query parameters.
"""

from __future__ import annotations

from sfdb.kg.query import KGQuery, KGQueryEngine
from sfdb.query.language import Query, QueryResult, QueryType


class KGQueryAdapter:
    """Adapts unified Query objects for the KG query engine."""

    def __init__(self, engine: KGQueryEngine) -> None:
        self._engine = engine

    def execute(self, query: Query) -> QueryResult:
        if query.type == QueryType.FACT:
            return self._execute_fact(query)
        if query.type == QueryType.WALK:
            return self._execute_walk(query)
        if query.type == QueryType.JOIN:
            return self._execute_join(query)
        raise ValueError(f"Unsupported query type: {query.type}")

    def _execute_fact(self, query: Query) -> QueryResult:
        kg_query = KGQuery(
            subject=query.pattern.subject if query.pattern else None,
            predicate=query.pattern.relation if query.pattern else None,
            limit=query.limit,
        )
        kg_result = self._engine.execute(kg_query)
        return QueryResult(
            facts=kg_result.facts,
            representation="kg",
        )

    def _execute_walk(self, query: Query) -> QueryResult:
        if query.start is None:
            raise ValueError("Walk query requires a start entity")
        if query.relation is None:
            raise ValueError("Walk query requires a relation")
        facts = self._engine.walk(query.start, query.relation, query.max_depth)
        return QueryResult(facts=facts, representation="kg")

    def _execute_join(self, query: Query) -> QueryResult:
        if query.relation is None:
            raise ValueError("Join query requires a relation")
        facts = self._engine.join(list(query.entities), query.relation)
        return QueryResult(facts=facts, representation="kg")
