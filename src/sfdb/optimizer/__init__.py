"""Query optimizer for the Semantic Fact Database.

Analyzes queries and selects the optimal execution strategy for
each representation (KG vs Sheaf). Provides cost estimates and
rewrite rules.

The optimizer is critical for fair benchmarking: it ensures that
both representations are queried in their optimal way, avoiding
artificially poor performance from either system.
"""

from sfdb.optimizer.optimizer import (
    CostEstimate,
    OptimizationRule,
    QueryOptimizer,
    QueryPlan,
)

__all__ = [
    "CostEstimate",
    "OptimizationRule",
    "QueryOptimizer",
    "QueryPlan",
]
