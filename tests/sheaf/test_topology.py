"""Tests for the sheaf topology module."""

from __future__ import annotations

from sfdb.sheaf.topology import FiniteTopologicalSpace, OpenSet


class TestOpenSet:
    def test_creation(self) -> None:
        os_ = OpenSet("test", frozenset({"a", "b"}))
        assert os_.name == "test"
        assert os_.points == frozenset({"a", "b"})

    def test_empty(self) -> None:
        os_ = OpenSet("empty")
        assert os_.points == frozenset()

    def test_contains(self) -> None:
        os_ = OpenSet("test", frozenset({"a"}))
        assert os_.contains("a")
        assert not os_.contains("b")

    def test_subset(self) -> None:
        small = OpenSet("s", frozenset({"a"}))
        large = OpenSet("l", frozenset({"a", "b"}))
        assert small.is_subset_of(large)
        assert not large.is_subset_of(small)

    def test_intersection(self) -> None:
        u = OpenSet("u", frozenset({"a", "b"}))
        v = OpenSet("v", frozenset({"b", "c"}))
        inter = u.intersect(v)
        assert inter.points == frozenset({"b"})

    def test_union(self) -> None:
        u = OpenSet("u", frozenset({"a"}))
        v = OpenSet("v", frozenset({"b"}))
        union = u.union(v)
        assert union.points == frozenset({"a", "b"})

    def test_hashable(self) -> None:
        u = OpenSet("u", frozenset({"a"}))
        d = {u: 1}
        assert d[u] == 1


class TestFiniteTopologicalSpace:
    def test_empty_space(self) -> None:
        X = FiniteTopologicalSpace()
        assert X.point_count() == 0
        assert X.open_set_count() == 0

    def test_add_open_set(self) -> None:
        X = FiniteTopologicalSpace()
        os_ = OpenSet("u", frozenset({"a", "b"}))
        X.add_open_set(os_)
        assert X.open_set_count() == 1
        assert X.point_count() == 2

    def test_get_open_set(self) -> None:
        X = FiniteTopologicalSpace()
        os_ = OpenSet("u", frozenset({"a"}))
        X.add_open_set(os_)
        assert X.get_open_set("u") == os_
        assert X.get_open_set("nonexistent") is None

    def test_contains_open_set(self) -> None:
        X = FiniteTopologicalSpace()
        X.add_open_set(OpenSet("u", frozenset()))
        assert X.contains_open_set("u")
        assert not X.contains_open_set("v")

    def test_neighborhoods(self) -> None:
        X = FiniteTopologicalSpace()
        os_ = OpenSet("u", frozenset({"a", "b"}))
        X.add_open_set(os_)
        nbs = X.neighborhoods("a")
        assert len(nbs) == 1
        assert nbs[0].center == "a"
        assert nbs[0].open_set == os_

    def test_minimal_open_set(self) -> None:
        X = FiniteTopologicalSpace()
        X.add_open_set(OpenSet("big", frozenset({"a", "b", "c"})))
        X.add_open_set(OpenSet("small", frozenset({"a", "b"})))
        minimal = X.minimal_open_set("a")
        assert minimal is not None
        assert minimal.name == "small"

    def test_intersection_closure(self) -> None:
        X = FiniteTopologicalSpace()
        X.add_open_set(OpenSet("u", frozenset({"a", "b", "c"})))
        X.add_open_set(OpenSet("v", frozenset({"b", "c", "d"})))
        X.intersection_closure()
        assert X.open_set_count() >= 2
        has_inter = any("∩" in name for name in X._open_sets)
        assert has_inter

    def test_remove_open_set(self) -> None:
        X = FiniteTopologicalSpace()
        X.add_open_set(OpenSet("u", frozenset({"a"})))
        X.remove_open_set("u")
        assert not X.contains_open_set("u")
        assert X.point_count() == 0
