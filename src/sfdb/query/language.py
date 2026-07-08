"""Unified query language for the Semantic Fact Database.

Design
------
The query language is representation-agnostic. A Query is a description
of what semantic information to retrieve, not how to retrieve it.

Both KGQueryEngine and SheafQueryEngine implement the QueryExecutor
protocol, so the same Query object can be dispatched to either system.

This is the key fairness mechanism: we run identical queries against
both representations and compare their outputs (semantic equivalence)
and performance (latency, memory, joins).

Query types
-----------
1. FactQuery: Retrieve facts matching a pattern.
2. WalkQuery: Traverse relationships from a starting entity.
3. JoinQuery: Find connections between entities.
4. GlueQuery (Sheaf-only): Reconstruct facts from sub-contexts.

Complexity
----------
Query dispatch: O(1).
Result comparison: O(n log m) for set difference on fact IDs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Protocol

from sfdb.common.types import Context, Fact, Identifier, Value


class QueryType(Enum):
    """The type of a query."""

    FACT = auto()
    WALK = auto()
    JOIN = auto()
    GLUE = auto()


@dataclass(slots=True, frozen=True)
class QueryPattern:
    """A pattern to match facts against.

    All fields are optional: None means "match anything".
    """

    subject: Identifier | None = None
    relation: Identifier | None = None
    objects: tuple[Value, ...] | None = None
    context: Context | None = None
    min_confidence: float = 0.0


@dataclass(slots=True, frozen=True)
class Query:
    """A unified semantic query.

    Parameters
    ----------
    type: The type of query.
    pattern: Pattern to match (for FACT queries).
    start: Starting entity (for WALK queries).
    relation: Relation to traverse (for WALK, JOIN queries).
    max_depth: Maximum traversal depth (for WALK).
    entities: Entity set (for JOIN queries).
    context: The context to query in.
    limit: Maximum results.
    """

    type: QueryType = QueryType.FACT
    pattern: QueryPattern | None = None
    start: Identifier | None = None
    relation: Identifier | None = None
    max_depth: int = 1
    entities: tuple[Identifier, ...] = ()
    context: Context | None = None
    limit: int = 0


@dataclass(slots=True)
class QueryResult:
    """The result of a unified query.

    Attributes
    ----------
    facts: The resulting facts.
    num_facts: Number of facts returned.
    execution_time_ns: Wall-clock time in nanoseconds.
    bytes_processed: Estimated bytes of data examined.
    representation: Which system produced the result ("kg" or "sheaf").
    """

    facts: list[Fact] = field(default_factory=list)
    execution_time_ns: int = 0
    bytes_processed: int = 0
    representation: str = ""

    @property
    def num_facts(self) -> int:
        return len(self.facts)


class QueryExecutor(Protocol):
    """Protocol that both KG and Sheaf query engines implement."""

    def execute(self, query: Query) -> QueryResult: ...


class QueryEngine:
    """Dispatches queries to either KG or Sheaf executor.

    This is the unified entry point for all queries in the benchmark.
    """

    def __init__(
        self, kg_executor: QueryExecutor | None = None, sheaf_executor: QueryExecutor | None = None
    ) -> None:
        self._kg = kg_executor
        self._sheaf = sheaf_executor

    def execute_kg(self, query: Query) -> QueryResult:
        if self._kg is None:
            raise RuntimeError("KG executor not configured")
        return self._kg.execute(query)

    def execute_sheaf(self, query: Query) -> QueryResult:
        if self._sheaf is None:
            raise RuntimeError("Sheaf executor not configured")
        return self._sheaf.execute(query)

    def execute_both(self, query: Query) -> tuple[QueryResult, QueryResult]:
        """Execute the same query on both systems and return both results."""
        kg_result = self.execute_kg(query)
        sheaf_result = self.execute_sheaf(query)
        return kg_result, sheaf_result

    @staticmethod
    def results_equivalent(r1: QueryResult, r2: QueryResult) -> bool:
        """Check if two results are semantically equivalent.

        Two results are equivalent iff they contain the same set of
        facts (by ID). Order does not matter.
        """
        ids1 = {f.id for f in r1.facts}
        ids2 = {f.id for f in r2.facts}
        return ids1 == ids2
