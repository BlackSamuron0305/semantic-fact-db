"""Round-trip tests for the SheafDatabaseEngine.

Verifies that SemanticFacts inserted into the sheaf database can be
retrieved exactly as originally specified (100% lossless).
"""

from __future__ import annotations

from datetime import UTC

import pytest

from common.interfaces import Query, QueryType
from common.schema import SemanticFact
from common.types import Context, Identifier, Provenance, TemporalInfo, Value
from sfdb.sheaf.engine import SheafDatabaseEngine


@pytest.fixture
def engine() -> SheafDatabaseEngine:
    eng = SheafDatabaseEngine()
    eng.create()
    return eng


class TestRoundTrip:
    def test_simple_fact(self, engine: SheafDatabaseEngine) -> None:
        original = SemanticFact(
            id=Identifier("rt1"),
            subject=Identifier("subj1"),
            relation=Identifier("Binary"),
            context=Context("default"),
            objects=(Value.literal("Alice"), Value.literal("Bob")),
            attributes={"subject": Value.literal("Alice"), "object": Value.literal("Bob")},
        )
        engine.insert(original)
        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj1"), limit=10)
        qr = engine.query(q)
        assert len(qr.facts) >= 1
        retrieved = qr.facts[0]
        assert retrieved.id == original.id
        assert retrieved.relation == original.relation
        assert retrieved.context == original.context

    def test_fact_with_attributes(self, engine: SheafDatabaseEngine) -> None:
        original = SemanticFact(
            id=Identifier("rt2"),
            subject=Identifier("subj2"),
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
        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj2"), limit=10)
        qr = engine.query(q)
        assert len(qr.facts) >= 1
        retrieved = qr.facts[0]
        assert retrieved.attributes["subject"] == Value.literal("Alice")

    def test_fact_with_provenance(self, engine: SheafDatabaseEngine) -> None:
        original = SemanticFact(
            id=Identifier("rt3"),
            subject=Identifier("subj3"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value.literal("x"),),
            provenance=Provenance(source="test_source", method="manual", confidence=0.95),
        )
        engine.insert(original)
        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj3"), limit=10)
        qr = engine.query(q)
        assert len(qr.facts) >= 1
        retrieved = qr.facts[0]
        assert retrieved.provenance.source == "test_source"
        assert retrieved.provenance.method == "manual"

    def test_fact_with_temporal(self, engine: SheafDatabaseEngine) -> None:
        from datetime import datetime

        original = SemanticFact(
            id=Identifier("rt4"),
            subject=Identifier("subj4"),
            relation=Identifier("Event"),
            context=Context("default"),
            objects=(Value.literal("temp"),),
            temporal=TemporalInfo(
                start=datetime(2024, 1, 1, tzinfo=UTC),
                end=datetime(2024, 12, 31, tzinfo=UTC),
            ),
        )
        engine.insert(original)
        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj4"), limit=10)
        qr = engine.query(q)
        assert len(qr.facts) >= 1
        retrieved = qr.facts[0]
        assert retrieved.temporal is not None
        assert retrieved.temporal.start == datetime(2024, 1, 1, tzinfo=UTC)

    def test_multiple_facts(self, engine: SheafDatabaseEngine) -> None:
        facts = [
            SemanticFact(
                id=Identifier(f"rt_batch_{i}"),
                subject=Identifier(f"subj_{i}"),
                relation=Identifier("Event"),
                context=Context("batch"),
                objects=(Value.literal(str(i)),),
            )
            for i in range(5)
        ]
        for f in facts:
            engine.insert(f)
        q = Query(query_type=QueryType.GLOBAL, limit=20)
        qr = engine.query(q)
        assert len(qr.facts) >= 5

    def test_export_import_roundtrip(self, engine: SheafDatabaseEngine) -> None:
        original = SemanticFact(
            id=Identifier("rt_exp"),
            subject=Identifier("subj_exp"),
            relation=Identifier("Test"),
            context=Context("special"),
            objects=(Value.literal("data"),),
            attributes={"key": Value.literal("value")},
            provenance=Provenance(source="roundtrip", method="export_test"),
        )
        engine.insert(original)
        data = engine.export()
        eng2 = SheafDatabaseEngine()
        eng2.create()
        count = eng2.import_data(data)
        assert count >= 1
        q = Query(query_type=QueryType.LOOKUP, subject=Identifier("subj_exp"), limit=10)
        qr = eng2.query(q)
        assert len(qr.facts) >= 1
        retrieved = qr.facts[0]
        assert retrieved.id == original.id
        assert retrieved.relation == original.relation
        assert retrieved.context == original.context
        assert retrieved.provenance.source == "roundtrip"
        eng2.drop()
