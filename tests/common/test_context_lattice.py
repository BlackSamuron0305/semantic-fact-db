"""Lattice-law tests for the context order.

Two parallel implementations of the context order exist:
``common.types.Context`` (engine data model) and
``sfdb.sheaf.sheaf.ContextPoset`` (presheaf layer). These tests pin the
shared convention from the paper (Definition "Context" and the open-set
intersection theorem): the root is maximal, more-specific contexts sit
below it, the join is the longest common prefix (most specific common
ancestor), and meets are partial — comparable pairs meet at the more
specific of the two, while incomparable contexts have no common
refinement at all.
"""

from common.types import Context as EngineContext
from sfdb.common.types import Context as SheafContext
from sfdb.sheaf.sheaf import ContextPoset


class TestEngineContextLattice:
    def test_meet_comparable_is_more_specific(self) -> None:
        broad = EngineContext("world.eu")
        narrow = EngineContext("world.eu.de")
        assert broad.meet(narrow) == narrow
        assert narrow.meet(broad) == narrow

    def test_meet_incomparable_is_none(self) -> None:
        assert EngineContext("world.eu").meet(EngineContext("world.us")) is None

    def test_join_is_longest_common_prefix(self) -> None:
        assert EngineContext("world.eu.de").join(EngineContext("world.eu.fr")) == EngineContext(
            "world.eu"
        )
        assert EngineContext("world.eu").join(EngineContext("world.us")) == EngineContext("world")

    def test_join_comparable_is_broader(self) -> None:
        broad = EngineContext("world.eu")
        narrow = EngineContext("world.eu.de")
        assert broad.join(narrow) == broad

    def test_join_disjoint_is_none(self) -> None:
        assert EngineContext("a.b").join(EngineContext("x.y")) is None

    def test_idempotence_and_commutativity(self) -> None:
        a = EngineContext("world.eu.de")
        b = EngineContext("world.us")
        assert a.meet(a) == a
        assert a.join(a) == a
        assert a.meet(b) == b.meet(a)
        assert a.join(b) == b.join(a)

    def test_absorption_where_meet_exists(self) -> None:
        a = EngineContext("world.eu.de")
        b = EngineContext("world.eu")
        m = a.meet(b)
        assert m is not None
        assert a.join(m) == a


class TestPosetLattice:
    def test_meet_matches_engine_convention(self) -> None:
        poset = ContextPoset()
        assert poset.meet(SheafContext("world.eu"), SheafContext("world.eu.de")) == SheafContext(
            "world.eu.de"
        )
        assert poset.meet(SheafContext("world.eu"), SheafContext("world.us")) is None

    def test_join_matches_engine_convention(self) -> None:
        poset = ContextPoset()
        de, fr = SheafContext("world.eu.de"), SheafContext("world.eu.fr")
        assert poset.join(de, fr) == SheafContext("world.eu")
        assert poset.join(SheafContext("a.b"), SheafContext("x.y")) is None

    def test_meet_join_commute(self) -> None:
        poset = ContextPoset()
        a = SheafContext("world.eu.de")
        b = SheafContext("world.us")
        assert poset.meet(a, b) == poset.meet(b, a)
        assert poset.join(a, b) == poset.join(b, a)


class TestIsCover:
    def _poset(self, *paths: str) -> ContextPoset:
        poset = ContextPoset()
        for path in paths:
            poset.add(SheafContext(path))
        return poset

    def test_children_covering_all_strict_descendants(self) -> None:
        poset = self._poset("world", "world.eu", "world.us", "world.eu.de")
        assert poset.is_cover(
            SheafContext("world"), [SheafContext("world.eu"), SheafContext("world.us")]
        )

    def test_missing_branch_is_not_a_cover(self) -> None:
        poset = self._poset("world", "world.eu", "world.us")
        assert not poset.is_cover(SheafContext("world"), [SheafContext("world.eu")])

    def test_non_subcontext_is_not_a_cover(self) -> None:
        poset = self._poset("world", "world.eu")
        assert not poset.is_cover(SheafContext("world.eu"), [SheafContext("world")])

    def test_empty_family_is_not_a_cover(self) -> None:
        poset = self._poset("world", "world.eu")
        assert not poset.is_cover(SheafContext("world"), [])
