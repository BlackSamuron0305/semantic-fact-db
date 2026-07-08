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

from common.interfaces import EngineStatistics, EngineType
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

    Uses real engine statistics for cost estimation instead of
    hardcoded heuristics.  The optimizer collects selectivity data
    from both engines and estimates costs based on actual cardinalities.

    The optimizer also collects statistics about the optimization process
    for the benchmark.
    """

    def __init__(
        self,
        kg_stats: EngineStatistics | None = None,
        sheaf_stats: EngineStatistics | None = None,
    ) -> None:
        self._kg_stats = kg_stats
        self._sheaf_stats = sheaf_stats
        self._rules: list[OptimizationRule] = []

    def update_statistics(
        self, kg_stats: EngineStatistics | None = None,
        sheaf_stats: EngineStatistics | None = None,
    ) -> None:
        """Update engine statistics for cost estimation."""
        if kg_stats is not None:
            self._kg_stats = kg_stats
        if sheaf_stats is not None:
            self._sheaf_stats = sheaf_stats

    def add_rule(self, rule: OptimizationRule) -> None:
        self._rules.append(rule)

    def estimate_cost_kg(self, query: Query) -> CostEstimate:
        """Estimate cost of executing query on KG using real statistics."""
        if self._kg_stats is None:
            return CostEstimate(total_cost=float("inf"))

        sel = self._kg_stats.selectivity
        triple_count = sel.get("triple_count", 0.0)
        entity_count = sel.get("entity_count", 1.0)
        avg_facts_per_entity = sel.get("avg_facts_per_entity", 1.0)
        avg_triples_per_fact = sel.get("avg_triples_per_fact", 1.0)

        scan_cost = triple_count

        join_cost = 0.0
        if query.type == QueryType.WALK:
            # Walk: each step follows avg_facts_per_entity edges
            join_cost = float(query.max_depth) * avg_facts_per_entity
        elif query.type == QueryType.JOIN:
            # Join: pairwise comparison of entity neighborhoods
            join_cost = float(len(query.entities)) ** 2 * avg_facts_per_entity

        # Reconstruction: each fact requires avg_triples_per_fact lookups
        reconstruction_cost = scan_cost * 0.1 * avg_triples_per_fact

        total = scan_cost + join_cost + reconstruction_cost
        return CostEstimate(
            scan_cost=scan_cost,
            join_cost=join_cost,
            reconstruction_cost=reconstruction_cost,
            total_cost=total,
        )

    def estimate_cost_sheaf(self, query: Query) -> CostEstimate:
        """Estimate cost of executing query on Sheaf DB using real statistics."""
        if self._sheaf_stats is None:
            return CostEstimate(total_cost=float("inf"))

        sel = self._sheaf_stats.selectivity
        section_count = sel.get("section_count", 0.0)
        context_count = sel.get("context_count", 1.0)
        avg_sections_per_context = sel.get("avg_sections_per_context", 1.0)
        avg_sections_per_fact = sel.get("avg_sections_per_fact", 1.0)

        if query.type in (QueryType.FACT, QueryType.WALK):
            # Sheaf only scans sections local to the context
            scan_cost = avg_sections_per_context
            join_cost = 0.0  # No decomposition → no joins needed
            reconstruction_cost = 0.0  # Sections are already complete
        elif query.type == QueryType.JOIN:
            # Joins still require scanning in sheaf, but can be
            # localized to specific contexts
            scan_cost = section_count
            join_cost = float(len(query.entities)) * avg_sections_per_context
            reconstruction_cost = 0.0
        elif query.type == QueryType.CONTEXT:
            # Context query: only scan the relevant context
            scan_cost = avg_sections_per_context
            join_cost = 0.0
            reconstruction_cost = 0.0
        elif query.type == QueryType.GLOBAL:
            # Global query: must scan everything and glue
            scan_cost = section_count
            join_cost = 0.0
            reconstruction_cost = section_count * 0.5  # gluing overhead
        else:
            scan_cost = section_count
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
