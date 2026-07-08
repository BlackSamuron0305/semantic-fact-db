"""Tests for the query optimizer."""

from common.interfaces import EngineStatistics, EngineType, Query, QueryType
from common.types import Identifier
from sfdb.optimizer.optimizer import CostEstimate, OptimizationRule, QueryOptimizer, QueryPlan


class TestCostEstimate:
    def test_construction(self) -> None:
        cost = CostEstimate(
            scan_cost=100.0, join_cost=50.0, reconstruction_cost=10.0, total_cost=160.0
        )
        assert cost.scan_cost == 100.0
        assert cost.total_cost == 160.0


class TestQueryOptimizer:
    def setup_method(self) -> None:
        kg_stats = EngineStatistics(
            total_facts=1000,
            total_entities=100,
            storage_bytes=0,
            index_count=4,
            engine_type=EngineType.KNOWLEDGE_GRAPH,
            selectivity={
                "triple_count": 1000.0,
                "entity_count": 100.0,
                "predicate_count": 10.0,
                "avg_facts_per_entity": 10.0,
                "avg_triples_per_fact": 3.0,
            },
        )
        sheaf_stats = EngineStatistics(
            total_facts=500,
            total_entities=500,
            storage_bytes=0,
            index_count=8,
            engine_type=EngineType.SHEAF_DATABASE,
            selectivity={
                "section_count": 500.0,
                "fact_count": 500.0,
                "context_count": 10.0,
                "avg_sections_per_context": 50.0,
                "avg_sections_per_fact": 1.0,
                "open_set_count": 20.0,
            },
        )
        self.optimizer = QueryOptimizer(kg_stats=kg_stats, sheaf_stats=sheaf_stats)

    def test_estimate_kg(self) -> None:
        q = Query(query_type=QueryType.LOOKUP, limit=100)
        cost = self.optimizer.estimate_cost_kg(q)
        assert cost.scan_cost > 0

    def test_estimate_sheaf(self) -> None:
        q = Query(query_type=QueryType.LOOKUP, limit=100)
        cost = self.optimizer.estimate_cost_sheaf(q)
        assert cost.scan_cost > 0
        assert cost.join_cost == 0  # Sheaf avoids joins for fact queries

    def test_select_plan(self) -> None:
        q = Query(query_type=QueryType.LOOKUP, limit=100)
        plan, kg_cost, sheaf_cost = self.optimizer.select_plan(q)
        assert isinstance(plan, QueryPlan)
        assert kg_cost.total_cost > 0
        assert sheaf_cost.total_cost > 0

    def test_rule_application(self) -> None:
        optimizer = QueryOptimizer()
        rule = OptimizationRule(
            name="test_rule",
            precondition=lambda q: q.query_type == QueryType.PATH,
            transform=lambda q: Query(query_type=QueryType.LOOKUP, subject=q.subject, limit=100),
        )
        optimizer.add_rule(rule)
        q = Query(query_type=QueryType.PATH, subject=Identifier("e1"), relation=Identifier("r1"), limit=100)
        result = rule.apply(q)
        assert result is not None
        assert result.query_type == QueryType.LOOKUP
