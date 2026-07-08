"""Tests for the KnowledgeGraphEngine."""

from __future__ import annotations

import pytest

from common.interfaces import EngineType, Query, QueryType
from common.schema import SemanticFact
from common.types import Context, Identifier, Value
from sfdb.kg.engine import KnowledgeGraphEngine


@pytest.fixture
def engine() -> KnowledgeGraphEngine:
    eng = KnowledgeGraphEngine()
    eng.create()
    return eng


def _lookup(engine: KnowledgeGraphEngine, fid: Identifier) -> SemanticFact | None:
    """Helper: lookup a fact by id through the ABC query interface."""
    q = Query(query_type=QueryType.LOOKUP, subject=fid, context="world")
    result = engine.query(q)
    return result.facts[0] if result.facts else None


class TestKnowledgeGraphEngine:
    def test_insert_and_verify(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("fact1"),
            subject=Identifier("fact1"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("Alice"), Value("runs")),
            attributes={"actor": Value("Alice"), "action": Value("runs")},
        )
        engine.insert(fact)
        vresult = engine.verify()
        assert vresult.valid is True

    def test_lookup_by_id(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("fact2"),
            subject=Identifier("fact2"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("Bob"), Value("jumps")),
            attributes={"actor": Value("Bob"), "action": Value("jumps")},
        )
        engine.insert(fact)
        result = _lookup(engine, Identifier("fact2"))
        assert result is not None
        assert result.id == Identifier("fact2")

    def test_lookup_nonexistent(self, engine: KnowledgeGraphEngine) -> None:
        result = _lookup(engine, Identifier("nonexistent"))
        assert result is None

    def test_delete(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("fact3"),
            subject=Identifier("fact3"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("Alice"), Value("sleeps")),
            attributes={"actor": Value("Alice"), "action": Value("sleeps")},
        )
        engine.insert(fact)
        engine.delete(Identifier("fact3"))
        result = _lookup(engine, Identifier("fact3"))
        assert result is None

    def test_context_query(self, engine: KnowledgeGraphEngine) -> None:
        for i in range(5):
            fact = SemanticFact(
                id=Identifier(f"ctx_fact_{i}"),
                subject=Identifier(f"ctx_subj_{i}"),
                relation=Identifier("Event"),
                context=Context("ctx_a"),
                objects=(Value(str(i)),),
                attributes={"val": Value(str(i))},
            )
            engine.insert(fact)
        q = Query(query_type=QueryType.CONTEXT, context="ctx_a")
        results = engine.query(q)
        assert len(results.facts) == 5

        q_other = Query(query_type=QueryType.CONTEXT, context="ctx_b")
        results_other = engine.query(q_other)
        assert len(results_other.facts) == 0

    def test_statistics(self, engine: KnowledgeGraphEngine) -> None:
        stats = engine.statistics()
        assert stats.total_facts == 0
        assert stats.engine_type == EngineType.KNOWLEDGE_GRAPH

        fact = SemanticFact(
            id=Identifier("stat_fact"),
            subject=Identifier("stat_fact"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("val"),),
            attributes={"attr": Value("val")},
        )
        engine.insert(fact)
        stats = engine.statistics()
        assert stats.total_facts > 0

    def test_clear(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("clear_fact"),
            subject=Identifier("clear_fact"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("y"),),
            attributes={"x": Value("y")},
        )
        engine.insert(fact)
        engine.drop()
        engine.create()
        result = _lookup(engine, Identifier("clear_fact"))
        assert result is None
        stats = engine.statistics()
        assert stats.total_facts == 0

    def test_fact_with_multiple_arguments(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("multi"),
            subject=Identifier("multi"),
            relation=Identifier("Relation"),
            context=Context("default"),
            objects=(Value.literal("Socrates"), Value.literal("human")),
            attributes={
                "subject": Value.literal("Socrates"),
                "predicate": Value.literal("is_a"),
                "object": Value.literal("human"),
            },
        )
        engine.insert(fact)
        result = _lookup(engine, Identifier("multi"))
        assert result is not None
        assert len(result.attributes) == 3
        assert result.attributes["subject"] == Value.literal("Socrates")

    def test_query_with_type_filter(self, engine: KnowledgeGraphEngine) -> None:
        fact_a = SemanticFact(
            id=Identifier("type_a"),
            subject=Identifier("type_a"),
            relation=Identifier("TypeA"),
            context=Context("default"),
            objects=(Value("a"),),
            attributes={"val": Value("a")},
        )
        fact_b = SemanticFact(
            id=Identifier("type_b"),
            subject=Identifier("type_b"),
            relation=Identifier("TypeB"),
            context=Context("default"),
            objects=(Value("b"),),
            attributes={"val": Value("b")},
        )
        engine.insert(fact_a)
        engine.insert(fact_b)
        q = Query(query_type=QueryType.LOOKUP, relation=Identifier("TypeA"))
        results = engine.query(q)
        assert len(results.facts) >= 1
