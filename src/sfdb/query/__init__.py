"""Common query language for both KG and Sheaf subsystems.

Defines a unified query interface that both representations accept.
This ensures benchmark fairness: the same query is executed against
both systems with identical semantics.

The query language supports:
    1. Fact pattern matching
    2. Context scoping
    3. Relation traversal
    4. Join operations
    5. Aggregation
"""

from sfdb.query.language import (
    Query,
    QueryEngine,
    QueryExecutor,
    QueryPattern,
    QueryResult,
)

__all__ = [
    "Query",
    "QueryEngine",
    "QueryExecutor",
    "QueryPattern",
    "QueryResult",
]
