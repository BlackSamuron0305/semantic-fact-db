"""Tests for the query planner and executor."""

from __future__ import annotations

import pytest

from common.schema import SemanticFact
from common.types import Context, Identifier, Value
from sfdb.kg.engine import KnowledgeGraphEngine
from sfdb.kg.planner import (
    JoinAlgorithm,
    LogicalFilter,
    LogicalIndexSeek,
    LogicalJoin,
    LogicalLimit,
    LogicalProject,
    LogicalScan,
    LogicalSort,
    PhysicalPlanBuilder,
    PlanExecutor,
)


class TestPhysicalPlanBuilder:
    def test_build_scan(self) -> None:
        plan = LogicalScan(alias="t")
        builder = PhysicalPlanBuilder()
        physical = builder.build(plan)
        assert physical is not None

    def test_build_index_seek(self) -> None:
        plan = LogicalIndexSeek(index="SPO", subject=1, predicate=2, obj=None, alias="t")
        builder = PhysicalPlanBuilder()
        physical = builder.build(plan)
        assert physical is not None

    def test_build_filter(self) -> None:
        inner = LogicalScan(alias="t")
        plan = LogicalFilter(condition="p = 2", child=inner)
        builder = PhysicalPlanBuilder()
        physical = builder.build(plan)
        assert physical is not None

    def test_build_join(self) -> None:
        left = LogicalScan(alias="a")
        right = LogicalScan(alias="b")
        plan = LogicalJoin(
            left=left,
            right=right,
            condition="a.s = b.s",
            algorithm=JoinAlgorithm.NESTED_LOOP,
        )
        builder = PhysicalPlanBuilder()
        physical = builder.build(plan)
        assert physical is not None

    def test_build_project(self) -> None:
        inner = LogicalScan(alias="t")
        plan = LogicalProject(columns=["s", "p", "o"], child=inner)
        builder = PhysicalPlanBuilder()
        physical = builder.build(plan)
        assert physical is not None

    def test_build_sort(self) -> None:
        inner = LogicalScan(alias="t")
        plan = LogicalSort(column="s", ascending=True, child=inner)
        builder = PhysicalPlanBuilder()
        physical = builder.build(plan)
        assert physical is not None

    def test_build_limit(self) -> None:
        inner = LogicalScan(alias="t")
        plan = LogicalLimit(limit=10, offset=0, child=inner)
        builder = PhysicalPlanBuilder()
        physical = builder.build(plan)
        assert physical is not None


@pytest.fixture
def engine() -> KnowledgeGraphEngine:
    eng = KnowledgeGraphEngine()
    eng.create()
    return eng


class TestPlanExecutor:
    def test_execute_scan(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("exec_scan"),
            subject=Identifier("exec_scan"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("y"),),
            attributes={"x": Value("y")},
        )
        engine.insert(fact)
        logical = LogicalScan(alias="t")
        builder = PhysicalPlanBuilder()
        physical = builder.build(logical)
        executor = PlanExecutor(
            lambda *args, **kwargs: (
                engine._indexes.scan_spo(None, None, None) if engine._indexes else []
            )
        )
        results = executor.execute(physical)
        assert len(results) > 0

    def test_execute_index_seek(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("exec_seek"),
            subject=Identifier("exec_seek"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("b"),),
            attributes={"a": Value("b")},
        )
        engine.insert(fact)
        logical = LogicalIndexSeek(index="SPO", subject=None, predicate=1, obj=None, alias="t")
        builder = PhysicalPlanBuilder()
        physical = builder.build(logical)
        executor = PlanExecutor(
            lambda *args, **kwargs: (
                engine._indexes.scan_spo(None, None, None) if engine._indexes else []
            )
        )
        results = executor.execute(physical)
        assert len(results) > 0

    def test_execute_project(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("exec_proj"),
            subject=Identifier("exec_proj"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("y"),),
            attributes={"x": Value("y")},
        )
        engine.insert(fact)
        inner = LogicalScan(alias="t")
        logical = LogicalProject(columns=("t.subject_id", "t.predicate_id"), child=inner)
        builder = PhysicalPlanBuilder()
        physical = builder.build(logical)
        executor = PlanExecutor(
            lambda *args, **kwargs: (
                engine._indexes.scan_spo(None, None, None) if engine._indexes else []
            )
        )
        results = executor.execute(physical)
        assert len(results) > 0
        assert len(list(results[0].keys())) == 2
