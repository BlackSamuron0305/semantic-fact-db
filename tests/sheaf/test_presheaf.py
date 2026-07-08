"""Tests for the sheaf presheaf module."""

from __future__ import annotations

import pytest

from common.schema import SemanticFact
from common.types import Context, Identifier, Value
from sfdb.sheaf.presheaf import LocalSection, Presheaf, Sheaf, Stalk
from sfdb.sheaf.topology import FiniteTopologicalSpace, OpenSet


@pytest.fixture
def fact() -> SemanticFact:
    return SemanticFact(
        id=Identifier("fact_1"),
        subject=Identifier("subj_1"),
        relation=Identifier("Event"),
        context=Context("default"),
        objects=(Value.literal("obj1"),),
        attributes={"key": Value.literal("val1")},
    )


class TestLocalSection:
    def test_creation(self, fact: SemanticFact) -> None:
        ls = LocalSection(fact=fact, open_set_name="event:fact_1")
        assert ls.fact.id == fact.id
        assert ls.open_set_name == "event:fact_1"


class TestStalk:
    def test_creation(self) -> None:
        stalk = Stalk("point_1")
        assert stalk.point_id == "point_1"
        assert stalk.section_count == 0

    def test_add_section(self, fact: SemanticFact) -> None:
        stalk = Stalk(fact.id.value)
        ls = LocalSection(fact=fact, open_set_name="event:fact_1")
        stalk.add_section(ls)
        assert stalk.section_count == 1
        retrieved = stalk.get_section(fact.id.value)
        assert retrieved is not None
        assert retrieved.fact == fact

    def test_remove_section(self, fact: SemanticFact) -> None:
        stalk = Stalk(fact.id.value)
        ls = LocalSection(fact=fact, open_set_name="event:fact_1")
        stalk.add_section(ls)
        stalk.remove_section(fact.id.value)
        assert stalk.section_count == 0


class TestPresheaf:
    @pytest.fixture
    def topology(self) -> FiniteTopologicalSpace:
        X = FiniteTopologicalSpace()
        X.add_open_set(OpenSet("event:f1", frozenset({"f1"})))
        X.add_open_set(OpenSet("event:f2", frozenset({"f2"})))
        X.add_open_set(OpenSet("entity:subj", frozenset({"f1", "f2"})))
        return X

    def test_assign(self, topology: FiniteTopologicalSpace) -> None:
        p = Presheaf(topology)
        f1 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("subj"),
            relation=Identifier("R"),
            context=Context("w"),
        )
        ls = LocalSection(fact=f1, open_set_name="event:f1")
        p.assign(ls)
        assert len(p.sections_over("event:f1")) == 1

    def test_sections_over(self, topology: FiniteTopologicalSpace) -> None:
        p = Presheaf(topology)
        f1 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("subj"),
            relation=Identifier("R"),
            context=Context("w"),
        )
        f2 = SemanticFact(
            id=Identifier("f2"),
            subject=Identifier("subj"),
            relation=Identifier("R"),
            context=Context("w"),
        )
        p.assign(LocalSection(fact=f1, open_set_name="entity:subj"))
        p.assign(LocalSection(fact=f2, open_set_name="entity:subj"))
        assert len(p.sections_over("entity:subj")) == 2


class TestSheaf:
    @pytest.fixture
    def topology(self) -> FiniteTopologicalSpace:
        X = FiniteTopologicalSpace()
        X.add_open_set(OpenSet("u", frozenset({"f1", "f2"})))
        X.add_open_set(OpenSet("v", frozenset({"f2", "f3"})))
        X.add_open_set(OpenSet("𝕌", frozenset({"f1", "f2", "f3"})))
        return X

    def test_global_sections(self, topology: FiniteTopologicalSpace) -> None:
        sheaf = Sheaf(topology)
        f2 = SemanticFact(
            id=Identifier("f2"),
            subject=Identifier("s"),
            relation=Identifier("R"),
            context=Context("w"),
        )
        sheaf.assign(LocalSection(fact=f2, open_set_name="u"))
        sheaf.assign(LocalSection(fact=f2, open_set_name="v"))
        global_sects = sheaf.compute_global_sections()
        assert len(global_sects) >= 1
        assert global_sects[0].fact.id == f2.id

    def test_restrict(self, topology: FiniteTopologicalSpace) -> None:
        sheaf = Sheaf(topology)
        f1 = SemanticFact(
            id=Identifier("f1"),
            subject=Identifier("s"),
            relation=Identifier("R"),
            context=Context("w"),
        )
        f2 = SemanticFact(
            id=Identifier("f2"),
            subject=Identifier("s"),
            relation=Identifier("R"),
            context=Context("w"),
        )
        sheaf.assign(LocalSection(fact=f1, open_set_name="u"))
        sheaf.assign(LocalSection(fact=f2, open_set_name="u"))
        sheaf.assign(LocalSection(fact=f2, open_set_name="v"))
        restricted = sheaf.restrict("u", "v")
        assert len(restricted) >= 1
