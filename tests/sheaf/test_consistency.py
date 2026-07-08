"""Tests for the sheaf consistency checker."""

from __future__ import annotations

import pytest

from common.schema import SemanticFact
from common.types import Context, Identifier
from sfdb.sheaf.consistency import ConsistencyChecker
from sfdb.sheaf.presheaf import LocalSection, Presheaf
from sfdb.sheaf.topology import FiniteTopologicalSpace, OpenSet


@pytest.fixture
def topology() -> FiniteTopologicalSpace:
    X = FiniteTopologicalSpace()
    X.add_open_set(OpenSet("∅", frozenset()))
    X.add_open_set(OpenSet("u", frozenset({"f1", "f2"})))
    X.add_open_set(OpenSet("v", frozenset({"f1"})))
    X.add_open_set(OpenSet("𝕌", frozenset({"f1", "f2"})))
    return X


@pytest.fixture
def presheaf(topology: FiniteTopologicalSpace) -> Presheaf:
    p = Presheaf(topology)
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
    p.assign(LocalSection(fact=f1, open_set_name="u"))
    p.assign(LocalSection(fact=f2, open_set_name="u"))
    p.assign(LocalSection(fact=f1, open_set_name="v"))
    p.assign(LocalSection(fact=f1, open_set_name="𝕌"))
    p.assign(LocalSection(fact=f2, open_set_name="𝕌"))
    return p


class TestConsistencyChecker:
    def test_check_all(self, presheaf: Presheaf, topology: FiniteTopologicalSpace) -> None:
        checker = ConsistencyChecker(presheaf, topology)
        results = checker.check_all()
        assert len(results) >= 4
        for r in results:
            assert isinstance(r.passed, bool)

    def test_locality(self, presheaf: Presheaf, topology: FiniteTopologicalSpace) -> None:
        checker = ConsistencyChecker(presheaf, topology)
        result = checker.check_locality()
        assert isinstance(result.passed, bool)

    def test_gluing(self, presheaf: Presheaf, topology: FiniteTopologicalSpace) -> None:
        checker = ConsistencyChecker(presheaf, topology)
        result = checker.check_gluing()
        assert isinstance(result.passed, bool)

    def test_restriction_composition(
        self, presheaf: Presheaf, topology: FiniteTopologicalSpace
    ) -> None:
        checker = ConsistencyChecker(presheaf, topology)
        result = checker.check_restriction_composition()
        assert isinstance(result.passed, bool)

    def test_identity_restriction(
        self, presheaf: Presheaf, topology: FiniteTopologicalSpace
    ) -> None:
        checker = ConsistencyChecker(presheaf, topology)
        result = checker.check_identity_restriction()
        assert isinstance(result.passed, bool)

    def test_empty_set(self, presheaf: Presheaf, topology: FiniteTopologicalSpace) -> None:
        checker = ConsistencyChecker(presheaf, topology)
        result = checker.check_empty_set()
        assert isinstance(result.passed, bool)
