"""Tests for the canonical model and mappings."""

from sfdb.canonical.canonical import (
    CanonicalEntity,
    CanonicalFact,
    CanonicalMapping,
    CanonicalModel,
    CanonicalRelation,
)
from sfdb.common.types import Fact, Identifier, Value


class TestCanonicalEntity:
    def test_construction(self) -> None:
        e = CanonicalEntity(id=Identifier("e1"), name="Alice")
        assert e.id.value == "e1"
        assert e.name == "Alice"

    def test_auto_id_on_none(self) -> None:
        id_val = Identifier()
        assert len(id_val.value) > 20  # Auto-generated UUID


class TestCanonicalRelation:
    def test_construction(self) -> None:
        r = CanonicalRelation(id=Identifier("knows"), arity=1)
        assert r.id.value == "knows"
        assert r.arity == 1


class TestCanonicalFact:
    def test_to_fact(self) -> None:
        e = CanonicalEntity(id=Identifier("alice"))
        r = CanonicalRelation(id=Identifier("knows"), arity=1)
        cf = CanonicalFact(
            subject=e,
            relation=r,
            objects=(Value.reference(Identifier("bob")),),
        )
        fact = cf.to_fact()
        assert fact.subject == Identifier("alice")
        assert fact.relation == Identifier("knows")
        assert len(fact.objects) == 1


class TestCanonicalMapping:
    def test_roundtrip(self) -> None:
        mapping = CanonicalMapping()
        entities = {Identifier("alice"): CanonicalEntity(id=Identifier("alice"))}
        relations = {Identifier("knows"): CanonicalRelation(id=Identifier("knows"), arity=1)}
        fact = Fact(
            id=Identifier("f1"),
            subject=Identifier("alice"),
            relation=Identifier("knows"),
            objects=(Value.reference(Identifier("bob")),),
        )
        canonical = mapping.to_canonical(fact, entities, relations)
        assert canonical.subject.id == Identifier("alice")
        assert canonical.relation.id == Identifier("knows")


class TestCanonicalModel:
    def test_add_entity(self) -> None:
        model = CanonicalModel()
        e = CanonicalEntity(id=Identifier("e1"))
        model.add_entity(e)
        assert len(model.entities) == 1

    def test_add_fact(self) -> None:
        model = CanonicalModel()
        e = CanonicalEntity(id=Identifier("alice"))
        r = CanonicalRelation(id=Identifier("knows"))
        cf = CanonicalFact(subject=e, relation=r)
        model.add_fact(cf)
        assert len(model.facts) == 1

    def test_equality(self) -> None:
        model1 = CanonicalModel()
        model2 = CanonicalModel()
        assert model1 == model2

        e = CanonicalEntity(id=Identifier("e1"))
        model1.add_entity(e)
        assert model1 != model2
