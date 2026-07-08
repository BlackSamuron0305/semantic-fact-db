"""Tests for the query optimizer."""

from __future__ import annotations

from sfdb.kg.optimizer import QueryOptimizer, TableStatistics
from sfdb.kg.planner import (
    JoinAlgorithm,
    LogicalFilter,
    LogicalIndexSeek,
    LogicalJoin,
    LogicalProject,
    LogicalScan,
)


class TestQueryOptimizer:
    def test_estimate_scan_cost(self) -> None:
        stats = TableStatistics(
            total_triples=1000, distinct_subjects=100, distinct_predicates=10, distinct_objects=500
        )
        opt = QueryOptimizer(stats)
        plan = LogicalScan(alias="t")
        cost = opt.estimate_cost(plan)
        assert cost > 0

    def test_estimate_index_seek_cost(self) -> None:
        stats = TableStatistics(total_triples=1000)
        opt = QueryOptimizer(stats)
        plan = LogicalIndexSeek(index="SPO", subject=1, predicate=2, obj=None, alias="t")
        cost = opt.estimate_cost(plan)
        assert cost > 0

    def test_estimate_filter_cost(self) -> None:
        stats = TableStatistics(total_triples=1000)
        opt = QueryOptimizer(stats)
        inner = LogicalScan(alias="t")
        plan = LogicalFilter(condition="p = 5", child=inner)
        cost = opt.estimate_cost(plan)
        assert cost > 0

    def test_explain_plan(self) -> None:
        stats = TableStatistics(total_triples=500)
        opt = QueryOptimizer(stats)
        plan = LogicalScan(alias="t")
        lines = opt.explain(plan)
        assert len(lines) > 0
        assert "SeqScan" in lines[0]

    def test_explain_filter(self) -> None:
        opt = QueryOptimizer()
        inner = LogicalScan(alias="t")
        plan = LogicalFilter(condition="p > 1", child=inner)
        lines = opt.explain(plan)
        assert any("Filter" in l for l in lines)

    def test_explain_join(self) -> None:
        opt = QueryOptimizer()
        left = LogicalScan(alias="a")
        right = LogicalScan(alias="b")
        plan = LogicalJoin(
            left=left,
            right=right,
            condition="a.s = b.s",
            algorithm=JoinAlgorithm.HASH_JOIN,
        )
        lines = opt.explain(plan)
        assert any("Join" in l for l in lines)

    def test_explain_project(self) -> None:
        opt = QueryOptimizer()
        inner = LogicalScan(alias="t")
        plan = LogicalProject(columns=["s"], child=inner)
        lines = opt.explain(plan)
        assert any("Project" in l for l in lines)

    def test_optimize_filter_pushdown(self) -> None:
        opt = QueryOptimizer()
        inner_scan = LogicalScan(alias="t")
        outer_filter = LogicalFilter(condition="p > 1", child=inner_scan)
        result = opt.optimize(outer_filter)
        assert isinstance(result, LogicalFilter)

    def test_get_estimated_rows_scan(self) -> None:
        stats = TableStatistics(total_triples=2000)
        opt = QueryOptimizer(stats)
        plan = LogicalScan(alias="t")
        rows = opt.get_estimated_rows(plan)
        assert rows == 2000
