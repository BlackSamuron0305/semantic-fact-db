"""Tests for SemanticFact invariant validation."""

from datetime import UTC

from common.schema import SemanticFact
from common.types import Identifier, Provenance, TemporalInfo, Value
from common.validation import check_fact_collection, check_fact_invariants


class TestSingleFactValidation:
    def test_valid_fact_passes(self) -> None:
        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("alice"),
            relation=Identifier("knows"),
        )
        errors = check_fact_invariants(fact)
        assert errors == []

    def test_empty_id(self) -> None:
        fact = SemanticFact(
            id=Identifier(""),
            subject=Identifier("s"),
            relation=Identifier("r"),
        )
        errors = check_fact_invariants(fact)
        assert any("id is empty" in e for e in errors)

    def test_empty_subject(self) -> None:
        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier(""),
            relation=Identifier("r"),
        )
        errors = check_fact_invariants(fact)
        assert any("subject is empty" in e for e in errors)

    def test_empty_relation(self) -> None:
        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier(""),
        )
        errors = check_fact_invariants(fact)
        assert any("relation is empty" in e for e in errors)

    def test_invalid_confidence(self) -> None:
        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            confidence=1.5,
        )
        errors = check_fact_invariants(fact)
        assert any("Confidence" in e for e in errors)

    def test_invalid_provenance_confidence(self) -> None:
        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=Provenance(confidence=2.0),
        )
        errors = check_fact_invariants(fact)
        assert any("Provenance confidence" in e for e in errors)

    def test_temporal_end_without_start(self) -> None:
        from datetime import datetime

        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            temporal=TemporalInfo(
                start=None,
                end=datetime(2024, 12, 31, tzinfo=UTC),
            ),
        )
        errors = check_fact_invariants(fact)
        assert any("Temporal end specified without start" in e for e in errors)

    def test_temporal_end_before_start(self) -> None:
        from datetime import datetime

        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            temporal=TemporalInfo(
                start=datetime(2024, 12, 31, tzinfo=UTC),
                end=datetime(2024, 1, 1, tzinfo=UTC),
            ),
        )
        errors = check_fact_invariants(fact)
        assert any("Temporal end precedes start" in e for e in errors)


class TestCollectionValidation:
    def test_valid_collection_passes(self) -> None:
        facts = [
            SemanticFact(id=Identifier("s1"), subject=Identifier("s1"), relation=Identifier("r")),
            SemanticFact(id=Identifier("s2"), subject=Identifier("s2"), relation=Identifier("r")),
            SemanticFact(id=Identifier("a"), subject=Identifier("s1"), relation=Identifier("r")),
            SemanticFact(id=Identifier("b"), subject=Identifier("s2"), relation=Identifier("r")),
        ]
        errors = check_fact_collection(facts)
        assert errors == []

    def test_duplicate_id_detected(self) -> None:
        facts = [
            SemanticFact(id=Identifier("dup"), subject=Identifier("s1"), relation=Identifier("r")),
            SemanticFact(id=Identifier("dup"), subject=Identifier("s2"), relation=Identifier("r")),
        ]
        errors = check_fact_collection(facts)
        assert any("Duplicate fact id" in e for e in errors)

    def test_missing_reference_detected(self) -> None:
        facts = [
            SemanticFact(
                id=Identifier("a"),
                subject=Identifier("bob"),
                relation=Identifier("knows"),
                objects=(Value.reference(Identifier("charlie")),),
            ),
        ]
        errors = check_fact_collection(facts)
        assert any("charlie" in e for e in errors)
