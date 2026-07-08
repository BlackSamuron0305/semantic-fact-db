"""Query optimization and cost estimation.

Mathematical background
-----------------------
The optimizer estimates the cost of executing a query on each
representation (KG vs Sheaf) and selects the optimal plan.

Cost model:

    Cost = α · scan_cost + β · join_cost + γ · reconstruction_cost

Where:
    - scan_cost: number of triples/sections examined
    - join_cost: number of pairwise comparisons for joins
    - reconstruction_cost: cost of reconstructing n-ary facts

For KG:
    scan_cost = |T| (total triples)
    join_cost ∝ |T|^d for d-way joins
    reconstruction_cost ∝ |R| (reified statements)

For Sheaf:
    scan_cost = |S_c| (sections local to context c)
    join_cost = 0 (no decomposition → no joins)
    reconstruction_cost = 0 (sections are already complete)

This model captures the key hypothesis: the sheaf representation
avoids decomposition overhead and join costs at the expense of
additional storage for context-indexed sections.

Complexity
----------
Cost estimation: O(1) (heuristic formula).
Plan selection: O(r) where r = number of rewrite rules.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

from sfdb.query.language import Query, QueryType


class QueryPlan(Enum):
    """The chosen execution plan."""

    KG_ONLY = auto()
    SHEAF_ONLY = auto()
    BOTH = auto()  # For verification/benchmark


@dataclass(slots=True, frozen=True)
class CostEstimate:
    """Estimated cost of executing a query on a representation.

    Attributes
    ----------
    scan_cost: Number of items to scan.
    join_cost: Number of join operations.
    reconstruction_cost: Number of reconstruction steps.
    total_cost: Weighted sum of all costs.
    """

    scan_cost: float = 0.0
    join_cost: float = 0.0
    reconstruction_cost: float = 0.0
    total_cost: float = 0.0


class OptimizationRule:
    """A rewrite rule that transforms a query to reduce cost.

    Each rule has a precondition (check if applicable) and a
    transformation (rewrite the query).
    """

    def __init__(
        self, name: str, precondition: Callable[[Query], bool], transform: Callable[[Query], Query]
    ) -> None:
        self.name = name
        self.precondition = precondition
        self.transform = transform

    def apply(self, query: Query) -> Query | None:
        if self.precondition(query):
            return self.transform(query)
        return None


class QueryOptimizer:
    """Optimizes queries by selecting the best plan and applying rewrites.

    The optimizer also collects statistics about the optimization process
    for the benchmark.
    """

    def __init__(
        self,
        kg_triples: int = 0,
        kg_entities: int = 0,
        sheaf_sections: int = 0,
        sheaf_contexts: int = 0,
    ) -> None:
        self._kg_triples = kg_triples
        self._kg_entities = kg_entities
        self._sheaf_sections = sheaf_sections
        self._sheaf_contexts = sheaf_contexts
        self._rules: list[OptimizationRule] = []

    def add_rule(self, rule: OptimizationRule) -> None:
        self._rules.append(rule)

    def estimate_cost_kg(self, query: Query) -> CostEstimate:
        """Estimate cost of executing query on KG."""
        scan_cost = float(self._kg_triples)
        join_cost = 0.0

        if query.type == QueryType.WALK:
            avg_degree = max(1.0, self._kg_triples / max(1, self._kg_entities))
            join_cost = float(query.max_depth) * avg_degree
        elif query.type == QueryType.JOIN:
            join_cost = float(len(query.entities)) ** 2

        reconstruction_cost = scan_cost * 0.1

        total = scan_cost + join_cost + reconstruction_cost
        return CostEstimate(
            scan_cost=scan_cost,
            join_cost=join_cost,
            reconstruction_cost=reconstruction_cost,
            total_cost=total,
        )

    def estimate_cost_sheaf(self, query: Query) -> CostEstimate:
        """Estimate cost of executing query on Sheaf DB."""
        if query.type in (QueryType.FACT, QueryType.WALK):
            # Sheaf only scans sections local to the context
            sections_per_context = max(
                1.0,
                self._sheaf_sections / max(1, self._sheaf_contexts),
            )
            scan_cost = sections_per_context
            join_cost = 0.0  # No decomposition → no joins needed
            reconstruction_cost = 0.0  # Sections are already complete
        elif query.type == QueryType.JOIN:
            # Joins still require scanning in sheaf, but can be
            # localized to specific contexts
            scan_cost = float(self._sheaf_sections)
            join_cost = float(len(query.entities))
            reconstruction_cost = 0.0
        else:
            scan_cost = float(self._sheaf_sections)
            join_cost = 0.0
            reconstruction_cost = 0.0

        total = scan_cost + join_cost + reconstruction_cost
        return CostEstimate(
            scan_cost=scan_cost,
            join_cost=join_cost,
            reconstruction_cost=reconstruction_cost,
            total_cost=total,
        )

    def select_plan(self, query: Query) -> tuple[QueryPlan, CostEstimate, CostEstimate]:
        """Select the optimal execution plan.

        Returns (plan, kg_cost, sheaf_cost).
        """
        # Apply rewrite rules
        rewritten = query
        for rule in self._rules:
            result = rule.apply(rewritten)
            if result is not None:
                rewritten = result

        kg_cost = self.estimate_cost_kg(rewritten)
        sheaf_cost = self.estimate_cost_sheaf(rewritten)

        if sheaf_cost.total_cost < kg_cost.total_cost:
            return QueryPlan.SHEAF_ONLY, kg_cost, sheaf_cost
        return QueryPlan.KG_ONLY, kg_cost, sheaf_cost
