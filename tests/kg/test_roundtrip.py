"""Tests for round-trip consistency of the Knowledge Graph engine.

Verifies that Facts inserted into the engine can be retrieved exactly
as originally specified (semantic equivalence).
"""

from __future__ import annotations

import pytest

from common.interfaces import Query, QueryType
from common.schema import SemanticFact
from common.types import Context, Identifier, Value
from sfdb.kg.engine import KnowledgeGraphEngine


@pytest.fixture
def engine() -> KnowledgeGraphEngine:
    eng = KnowledgeGraphEngine()
    eng.create()
    return eng


def _lookup(engine: KnowledgeGraphEngine, fid: Identifier) -> SemanticFact | None:
    q = Query(query_type=QueryType.LOOKUP, subject=fid, context="world")
    result = engine.query(q)
    return result.facts[0] if result.facts else None


class TestRoundTrip:
    def test_simple_binary_fact(self, engine: KnowledgeGraphEngine) -> None:
        original = SemanticFact(
            id=Identifier("rt1"),
            subject=Identifier("rt1"),
            relation=Identifier("Binary"),
            context=Context("default"),
            objects=(Value.literal("Alice"), Value.literal("Bob")),
            attributes={"subject": Value.literal("Alice"), "object": Value.literal("Bob")},
        )
        engine.insert(original)
        retrieved = _lookup(engine, Identifier("rt1"))
        assert retrieved is not None
        assert retrieved.id == original.id
        assert retrieved.relation == original.relation
        assert retrieved.context == original.context
        assert retrieved.attributes == original.attributes

    def test_fact_with_three_arguments(self, engine: KnowledgeGraphEngine) -> None:
        original = SemanticFact(
            id=Identifier("rt2"),
            subject=Identifier("rt2"),
            relation=Identifier("Triple"),
            context=Context("ctx1"),
            objects=(Value.literal("Alice"), Value.literal("Bob")),
            attributes={
                "subject": Value.literal("Alice"),
                "predicate": Value.literal("knows"),
                "object": Value.literal("Bob"),
            },
        )
        engine.insert(original)
        retrieved = _lookup(engine, Identifier("rt2"))
        assert retrieved is not None
        assert retrieved.attributes["subject"] == Value.literal("Alice")
        assert retrieved.attributes["predicate"] == Value.literal("knows")
        assert retrieved.attributes["object"] == Value.literal("Bob")

    def test_fact_with_identifier_arguments(self, engine: KnowledgeGraphEngine) -> None:
        original = SemanticFact(
            id=Identifier("rt3"),
            subject=Identifier("rt3"),
            relation=Identifier("Relation"),
            context=Context("default"),
            objects=(
                Value.reference(Identifier("EntityA")),
                Value.reference(Identifier("EntityB")),
            ),
            attributes={
                "source": Value.reference(Identifier("EntityA")),
                "target": Value.reference(Identifier("EntityB")),
            },
        )
        engine.insert(original)
        retrieved = _lookup(engine, Identifier("rt3"))
        assert retrieved is not None
        assert retrieved.attributes["source"] == Value.reference(Identifier("EntityA"))
        assert retrieved.attributes["target"] == Value.reference(Identifier("EntityB"))

    def test_multiple_facts_round_trip(self, engine: KnowledgeGraphEngine) -> None:
        facts = [
            SemanticFact(
                id=Identifier(f"rt_batch_{i}"),
                subject=Identifier(f"rt_batch_{i}"),
                relation=Identifier("Event"),
                context=Context("batch"),
                objects=(Value.literal(str(i)),),
                attributes={"val": Value.literal(str(i))},
            )
            for i in range(10)
        ]
        for f in facts:
            engine.insert(f)
        for f in facts:
            retrieved = _lookup(engine, f.id)
            assert retrieved is not None
            assert retrieved.attributes == f.attributes

    def test_reinsert_same_fact(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("rt_dup"),
            subject=Identifier("rt_dup"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value.literal("value"),),
            attributes={"key": Value.literal("value")},
        )
        engine.insert(fact)
        engine.insert(fact)
        retrieved = _lookup(engine, Identifier("rt_dup"))
        assert retrieved is not None
        assert retrieved.attributes["key"] == Value.literal("value")

    def test_clear_and_reinsert(self, engine: KnowledgeGraphEngine) -> None:
        fact = SemanticFact(
            id=Identifier("rt_clear"),
            subject=Identifier("rt_clear"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value("y"),),
            attributes={"x": Value("y")},
        )
        engine.insert(fact)
        engine.drop()
        engine.create()
        engine.insert(fact)
        retrieved = _lookup(engine, Identifier("rt_clear"))
        assert retrieved is not None
