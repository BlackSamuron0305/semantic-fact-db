"""Adapter that maps unified Queries to SheafQueryEngine calls.

This adapter enables the QueryEngine to dispatch unified queries
to the Sheaf Database subsystem.

Complexity
----------
Adaptation: O(1) — direct mapping of query parameters.
"""

from __future__ import annotations

from sfdb.query.language import Query, QueryResult, QueryType
from sfdb.sheaf.query import SheafQuery, SheafQueryEngine


class SheafQueryAdapter:
    """Adapts unified Query objects for the Sheaf query engine."""

    def __init__(self, engine: SheafQueryEngine) -> None:
        self._engine = engine

    def execute(self, query: Query) -> QueryResult:
        if query.type == QueryType.FACT:
            return self._execute_fact(query)
        if query.type == QueryType.WALK:
            return self._execute_walk(query)
        if query.type == QueryType.GLUE:
            return self._execute_glue(query)
        raise ValueError(f"Unsupported query type: {query.type}")

    def _execute_fact(self, query: Query) -> QueryResult:
        sheaf_query = SheafQuery(
            context=query.context or (query.pattern.context if query.pattern else None),
            subject=query.pattern.subject if query.pattern else None,
            relation=query.pattern.relation if query.pattern else None,
            include_restricted=True,
            limit=query.limit,
        )
        result = self._engine.execute(sheaf_query)
        return QueryResult(
            facts=result.facts,
            representation="sheaf",
        )

    def _execute_walk(self, query: Query) -> QueryResult:
        ctx = query.context or None
        if query.start is None:
            raise ValueError("Walk query requires a start entity")
        facts = self._engine.search_subject(query.start, ctx)
        return QueryResult(facts=facts, representation="sheaf")

    def _execute_glue(self, query: Query) -> QueryResult:
        raise NotImplementedError("Glue query requires sub-context fact mapping")
