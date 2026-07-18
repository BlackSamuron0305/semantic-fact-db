"""Query planner for the sheaf database.

The SheafQueryPlanner translates logical Query objects into sequences
of restriction operations, local section retrievals, and (if needed)
global reconstruction — instead of graph traversals.

Query execution follows the classification from the optimizer:
- Local: retrieve from a single stalk
- Semi-local: restrict from one open set to relevant sub-sets
- Global: compute global sections via gluing
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from common.interfaces import (
    Query,
    QueryResult,
    QueryType,
)
from common.schema import SemanticFact
from common.types import Context
from sfdb.sheaf.indexes import GlobalSectionCache, StalkIndex, parse_temporal_bound
from sfdb.sheaf.optimizer import QueryClassification, SheafOptimizer
from sfdb.sheaf.presheaf import GlobalSection, LocalSection, Presheaf
from sfdb.sheaf.restriction import RestrictionGraph

_parse_temporal_token = parse_temporal_bound


def _temporal_query_bounds(
    start_token: str | None, end_token: str | None
) -> tuple[datetime | None, datetime | None]:
    """Resolve a query's temporal_start/temporal_end into concrete bounds.

    A bare-year start with no end is shorthand for that whole year,
    e.g. temporal_start="2024" alone means [2024-01-01, 2025-01-01).
    """
    q_start = _parse_temporal_token(start_token) if start_token else None
    q_end = _parse_temporal_token(end_token) if end_token else None
    if q_start is not None and q_end is None and len(start_token) == 4 and start_token.isdigit():
        q_end = datetime(q_start.year + 1, 1, 1, tzinfo=UTC)
    return q_start, q_end


@dataclass
class SheafPlanStep:
    """One step in a sheaf query execution plan."""

    operation: str
    target: str = ""
    detail: str = ""
    estimated_cost: float = 1.0

    def __repr__(self) -> str:
        return f"{self.operation}({self.target})"


class SheafQueryPlanner:
    """Plans and executes queries against a sheaf database.

    The planner interprets each Query as a sequence of:
    1. Classification (local/semi-local/global)
    2. Open set selection
    3. Section retrieval (with optional restriction)
    4. Optional: global reconstruction

    Usage::

        planner = SheafQueryPlanner(presheaf, optimizer, cache)
        plan = planner.plan(query)
        result = planner.execute(plan, query)
    """

    def __init__(
        self,
        presheaf: Presheaf,
        optimizer: SheafOptimizer,
        cache: GlobalSectionCache,
        restriction_graph: RestrictionGraph,
        stalk_index: StalkIndex | None = None,
    ) -> None:
        self._presheaf = presheaf
        self._optimizer = optimizer
        self._cache = cache
        self._restriction_graph = restriction_graph
        self._stalk_index = stalk_index

    def plan(self, query: Query) -> SheafPlan:
        """Produce an execution plan for *query*."""
        steps: list[SheafPlanStep] = []
        classification = self._optimizer.classify(query)
        steps.append(
            SheafPlanStep(
                operation="classify",
                detail=f"{classification.level} ({len(classification.target_open_sets)} candidate sets)",
            )
        )

        if classification.level == QueryClassification.LOCAL:
            open_sets = self._optimizer.optimize(query, classification)
            for os_name in open_sets:
                steps.append(
                    SheafPlanStep(
                        operation="local_retrieve",
                        target=os_name,
                        detail=f"Retrieve sections from {os_name}",
                    )
                )

        elif classification.level == QueryClassification.SEMI_LOCAL:
            origin = classification.target_open_sets[:1]
            for origin_os in origin:
                for target_name in self._restriction_graph.get_targets(origin_os):
                    steps.append(
                        SheafPlanStep(
                            operation="restrict",
                            target=f"{origin_os}→{target_name}",
                            detail=f"Restrict {origin_os} to {target_name}",
                        )
                    )

        elif classification.level == QueryClassification.GLOBAL:
            steps.append(
                SheafPlanStep(
                    operation="global_reconstruct",
                    detail="Compute global sections via sheaf gluing",
                    estimated_cost=50.0,
                )
            )

        steps.append(
            SheafPlanStep(
                operation="filter_and_limit",
                detail=f"Apply limit={query.limit}, offset={query.offset}",
            )
        )

        total_cost = sum(s.estimated_cost for s in steps)
        return SheafPlan(
            classification=classification,
            steps=tuple(steps),
            estimated_cost=total_cost,
        )

    def execute(self, plan: SheafPlan, query: Query) -> QueryResult:
        """Execute a plan and return results."""
        t0 = time.perf_counter_ns()
        facts: list[SemanticFact] = []

        classification = plan.classification

        if classification.level == QueryClassification.LOCAL:
            for os_name in classification.target_open_sets[:1]:
                sections = self._presheaf.sections_over(os_name)
                if query.subject is not None:
                    sections = [
                        s
                        for s in sections
                        if s.fact.subject.value == query.subject.value
                        or s.fact.id.value == query.subject.value
                    ]
                for s in sections[: query.limit]:
                    facts.append(s.fact)

        elif classification.level == QueryClassification.SEMI_LOCAL:
            all_sections: dict[str, LocalSection] = {}
            for os_name in classification.target_open_sets:
                for section in self._presheaf.sections_over(os_name):
                    all_sections[section.fact.id.value] = section
                    self._cache.add(GlobalSection(fact=section.fact, consistency_verified=True))
            for section in all_sections.values():
                if self._matches_query(section.fact, query):
                    facts.append(section.fact)
            facts = facts[: query.limit]

        elif classification.level == QueryClassification.GLOBAL:
            # Return all unique facts via the flat stalk index (O(N) in the
            # number of facts) instead of enumerating every open set, which
            # would revisit each fact once per open set it belongs to.
            if self._stalk_index is not None:
                for stalk in self._stalk_index.all_stalks():
                    for ls in stalk.sections.values():
                        if self._matches_query(ls.fact, query):
                            facts.append(ls.fact)
            else:
                seen: set[str] = set()
                for sections in self._presheaf._sections_by_openset.values():
                    for ls in sections.values():
                        if ls.fact.id.value not in seen:
                            seen.add(ls.fact.id.value)
                            if self._matches_query(ls.fact, query):
                                facts.append(ls.fact)

        facts = facts[query.offset : query.offset + query.limit]
        ns = time.perf_counter_ns() - t0
        return QueryResult(
            facts=tuple(facts),
            execution_time_ns=ns,
            rows_scanned=len(facts),
        )

    def _matches_query(self, fact: SemanticFact, query: Query) -> bool:
        if query.subject is not None and fact.subject != query.subject:
            return False
        if query.relation is not None and fact.relation != query.relation:
            return False
        if query.query_type == QueryType.TEMPORAL and (query.temporal_start or query.temporal_end):
            if fact.temporal is None:
                return False
            q_start, q_end = _temporal_query_bounds(query.temporal_start, query.temporal_end)
            f_start, f_end = fact.temporal.start, fact.temporal.end
            if q_end is not None and f_start is not None and f_start >= q_end:
                return False
            if q_start is not None and f_end is not None and f_end <= q_start:
                return False
        if query.context == "world":
            return True
        # A query anchored at a broader context should also match facts
        # stated in any of its sub-contexts (the topology builder adds
        # ancestor open sets for exactly this reason).
        return fact.context.is_subcontext(Context(query.context))


@dataclass(frozen=True)
class SheafPlan:
    """An execution plan for the sheaf database."""

    classification: QueryClassification
    steps: tuple[SheafPlanStep, ...] = field(default_factory=tuple)
    estimated_cost: float = 0.0

    def __repr__(self) -> str:
        return f"SheafPlan({self.classification.level}, cost={self.estimated_cost:.1f}, {len(self.steps)} steps)"
