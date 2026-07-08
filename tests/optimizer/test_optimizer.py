"""Tests for the query optimizer."""

from sfdb.common.types import Identifier
from sfdb.optimizer.optimizer import CostEstimate, OptimizationRule, QueryOptimizer, QueryPlan
from sfdb.query.language import Query, QueryPattern, QueryType


class TestCostEstimate:
    def test_construction(self) -> None:
        cost = CostEstimate(
            scan_cost=100.0, join_cost=50.0, reconstruction_cost=10.0, total_cost=160.0
        )
        assert cost.scan_cost == 100.0
        assert cost.total_cost == 160.0


class TestQueryOptimizer:
    def setup_method(self) -> None:
        self.optimizer = QueryOptimizer(
            kg_triples=1000,
            kg_entities=100,
            sheaf_sections=500,
            sheaf_contexts=10,
        )

    def test_estimate_kg(self) -> None:
        q = Query(type=QueryType.FACT, pattern=QueryPattern())
        cost = self.optimizer.estimate_cost_kg(q)
        assert cost.scan_cost > 0

    def test_estimate_sheaf(self) -> None:
        q = Query(type=QueryType.FACT, pattern=QueryPattern())
        cost = self.optimizer.estimate_cost_sheaf(q)
        assert cost.scan_cost > 0
        assert cost.join_cost == 0  # Sheaf avoids joins for fact queries

    def test_select_plan(self) -> None:
        q = Query(type=QueryType.FACT, pattern=QueryPattern())
        plan, kg_cost, sheaf_cost = self.optimizer.select_plan(q)
        assert isinstance(plan, QueryPlan)
        assert kg_cost.total_cost > 0
        assert sheaf_cost.total_cost > 0

    def test_rule_application(self) -> None:
        optimizer = QueryOptimizer()
        rule = OptimizationRule(
            name="test_rule",
            precondition=lambda q: q.type == QueryType.WALK,
            transform=lambda q: Query(type=QueryType.FACT, pattern=QueryPattern(subject=q.start)),
        )
        optimizer.add_rule(rule)
        # Test rule via the rewrite mechanism
        q = Query(type=QueryType.WALK, start=Identifier("e1"), relation=Identifier("r1"))
        result = rule.apply(q)
        assert result is not None
        assert result.type == QueryType.FACT
