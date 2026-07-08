"""Tests for the SemanticFact canonical schema."""

from common.schema import SemanticFact
from common.types import Context, Identifier, Provenance, TemporalInfo, Value


class TestSemanticFactConstruction:
    def test_minimal_fact(self) -> None:
        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("alice"),
            relation=Identifier("knows"),
        )
        assert fact.id.value == "f1"
        assert fact.subject.value == "alice"
        assert fact.relation.value == "knows"
        assert fact.objects == ()
        assert fact.arity() == 0
        assert fact.confidence == 1.0

    def test_nary_fact(self) -> None:
        fact = SemanticFact(
            id=Identifier("f2"),
            subject=Identifier("alice"),
            relation=Identifier("signed"),
            objects=(
                Value.reference(Identifier("contract-42")),
                Value.literal("2024-03-15"),
                Value.reference(Identifier("acme-corp")),
            ),
        )
        assert fact.arity() == 3

    def test_fact_with_all_fields(self) -> None:
        fact = SemanticFact(
            id=Identifier("f3"),
            subject=Identifier("bob"),
            relation=Identifier("employed_by"),
            objects=(Value.reference(Identifier("acme-corp")),),
            attributes={"since": Value.literal("2020-01-01")},
            context=Context("world.employment"),
            provenance=Provenance(source="hr-system", method="import"),
            confidence=0.95,
            temporal=TemporalInfo(start=None, end=None),
            metadata={"batch_id": "batch-007"},
        )
        assert fact.attributes["since"].inner == "2020-01-01"
        assert fact.provenance.source == "hr-system"
        assert fact.metadata["batch_id"] == "batch-007"

    def test_frozen(self) -> None:
        import pytest

        fact = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
        )
        with pytest.raises(AttributeError):
            fact.subject = Identifier("x")  # type: ignore[attr-defined]

    def test_confidence_validation(self) -> None:
        f_high = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            confidence=1.5,
        )
        f_low = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            confidence=-0.1,
        )
        from common.validation import check_fact_invariants

        errs_high = check_fact_invariants(f_high)
        errs_low = check_fact_invariants(f_low)
        assert any("Confidence" in e for e in errs_high)
        assert any("Confidence" in e for e in errs_low)


class TestSemanticFactEquality:
    def test_equal_facts(self) -> None:
        prov = Provenance(source="test", method="test")
        f1 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
        )
        f2 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
        )
        assert f1 == f2

    def test_different_ids(self) -> None:
        prov = Provenance(source="test", method="test")
        f1 = SemanticFact(
            id=Identifier("a"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
        )
        f2 = SemanticFact(
            id=Identifier("b"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
        )
        assert f1 != f2

    def test_metadata_excluded_from_equality(self) -> None:
        prov = Provenance(source="test", method="test")
        f1 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
            metadata={"extra": 1},
        )
        f2 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
            metadata={"extra": 2},
        )
        assert f1 == f2  # metadata is not compared


class TestSemanticFactHashing:
    def test_hashable(self) -> None:
        f1 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
        )
        d = {f1: "value"}
        assert d[f1] == "value"

    def test_hash_matches_equality(self) -> None:
        prov = Provenance(source="test", method="test")
        f1 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
        )
        f2 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("r"),
            provenance=prov,
        )
        assert hash(f1) == hash(f2)
