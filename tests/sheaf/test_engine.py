"""Tests for the SheafDatabaseEngine."""

from __future__ import annotations

import pytest

from common.interfaces import EngineType, Query, QueryType
from common.schema import SemanticFact
from common.types import Context, Identifier, Value
from sfdb.sheaf.engine import SheafDatabaseEngine


@pytest.fixture
def engine() -> SheafDatabaseEngine:
    eng = SheafDatabaseEngine()
    eng.create()
    return eng


class TestSheafDatabaseEngine:
    def test_create_and_drop(self) -> None:
        eng = SheafDatabaseEngine()
        eng.create()
        assert eng.engine_type == EngineType.SHEAF_DATABASE
        eng.drop()

    def test_insert_and_query_lookup(self, engine: SheafDatabaseEngine) -> None:
        fact = SemanticFact(
            id=Identifier("sf1"),
            subject=Identifier("subj1"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value.literal("obj1"),),
            attributes={"key": Value.literal("val1")},
        )
        result = engine.insert(fact)
        assert result.success

        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj1"), limit=10)
        qr = engine.query(q)
        assert len(qr.facts) >= 1
        assert qr.facts[0].id == fact.id

    def test_insert_and_query_context(self, engine: SheafDatabaseEngine) -> None:
        fact = SemanticFact(
            id=Identifier("sf2"),
            subject=Identifier("subj2"),
            relation=Identifier("Test"),
            context=Context("custom"),
            objects=(Value.literal("x"),),
            attributes={"a": Value.literal("b")},
        )
        engine.insert(fact)
        q = Query(query_type=QueryType.CONTEXT, context="custom", limit=10)
        qr = engine.query(q)
        assert len(qr.facts) >= 1

    def test_delete(self, engine: SheafDatabaseEngine) -> None:
        fact = SemanticFact(
            id=Identifier("sf_del"),
            subject=Identifier("subj_del"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(),
        )
        engine.insert(fact)
        dr = engine.delete(Identifier("sf_del"))
        assert dr.success

        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj_del"), limit=10)
        qr = engine.query(q)
        assert len(qr.facts) == 0

    def test_update(self, engine: SheafDatabaseEngine) -> None:
        old = SemanticFact(
            id=Identifier("sf_upd"),
            subject=Identifier("subj_upd"),
            relation=Identifier("Old"),
            context=Context("default"),
        )
        engine.insert(old)

        new = SemanticFact(
            id=Identifier("sf_upd"),
            subject=Identifier("subj_upd"),
            relation=Identifier("New"),
            context=Context("default"),
        )
        ur = engine.update(Identifier("sf_upd"), new)
        assert ur.success

        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj_upd"), limit=10)
        qr = engine.query(q)
        assert len(qr.facts) >= 1
        assert qr.facts[0].relation == Identifier("New")

    def test_statistics(self, engine: SheafDatabaseEngine) -> None:
        stats = engine.statistics()
        assert stats.engine_type == EngineType.SHEAF_DATABASE
        assert isinstance(stats.total_facts, int)

    def test_verify(self, engine: SheafDatabaseEngine) -> None:
        v = engine.verify()
        assert isinstance(v.valid, bool)

    def test_explain(self, engine: SheafDatabaseEngine) -> None:
        q = Query(query_type=QueryType.GLOBAL, limit=5)
        plan = engine.explain(q)
        assert len(plan.steps) >= 1
        assert plan.estimated_cost > 0

    def test_export_import(self, engine: SheafDatabaseEngine) -> None:
        fact = SemanticFact(
            id=Identifier("sf_exp"),
            subject=Identifier("subj_exp"),
            relation=Identifier("Event"),
            context=Context("default"),
        )
        engine.insert(fact)
        data = engine.export()
        assert len(data) > 0

        eng2 = SheafDatabaseEngine()
        eng2.create()
        count = eng2.import_data(data)
        assert count >= 1

        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj_exp"), limit=10)
        qr = eng2.query(q)
        assert len(qr.facts) >= 1
        eng2.drop()

    def test_global_query(self, engine: SheafDatabaseEngine) -> None:
        for i in range(3):
            fact = SemanticFact(
                id=Identifier(f"g{i}"),
                subject=Identifier(f"subj{i}"),
                relation=Identifier("Event"),
                context=Context("default"),
                objects=(Value.literal(str(i)),),
            )
            engine.insert(fact)
        q = Query(query_type=QueryType.GLOBAL, limit=10)
        qr = engine.query(q)
        assert len(qr.facts) == 3

    def test_benchmark_stats(self, engine: SheafDatabaseEngine) -> None:
        stats = engine.benchmark_stats()
        assert isinstance(stats, dict)
        assert "construction_count" in stats
