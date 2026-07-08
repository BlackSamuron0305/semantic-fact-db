"""Tests for the sheaf restriction module."""

from __future__ import annotations

from common.types import Context
from sfdb.sheaf.restriction import (
    ContextRestriction,
    RestrictionGraph,
    RestrictionMap,
    TemporalRestriction,
)


class TestRestrictionMap:
    def test_creation(self) -> None:
        r = RestrictionMap(source_name="u", target_name="v")
        assert r.source_name == "u"
        assert r.target_name == "v"
        assert r.key == ("u", "v")

    def test_repr(self) -> None:
        r = RestrictionMap(source_name="big", target_name="small")
        assert "big" in repr(r)
        assert "small" in repr(r)


class TestContextRestriction:
    def test_creation(self) -> None:
        c = Context("world.2024")
        d = Context("world")
        cr = ContextRestriction(source_context=c, target_context=d)
        assert cr.is_valid

    def test_repr(self) -> None:
        cr = ContextRestriction(source_context=Context("a.b"), target_context=Context("a"))
        assert "a.b" in repr(cr)


class TestTemporalRestriction:
    def test_creation(self) -> None:
        tr = TemporalRestriction(
            source_start="2024",
            source_end="2025",
            target_start="2024",
            target_end="2024",
        )
        assert tr.source_start == "2024"


class TestRestrictionGraph:
    def test_empty(self) -> None:
        g = RestrictionGraph()
        assert g.node_count() == 0
        assert g.edge_count() == 0

    def test_add_edge(self) -> None:
        g = RestrictionGraph()
        g.add_edge("big", "small")
        assert g.edge_count() == 1
        assert "small" in g.get_targets("big")

    def test_path_exists(self) -> None:
        g = RestrictionGraph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        assert g.path_exists("a", "c")
        assert not g.path_exists("c", "a")

    def test_get_sources(self) -> None:
        g = RestrictionGraph()
        g.add_edge("a", "c")
        g.add_edge("b", "c")
        sources = g.get_sources("c")
        assert "a" in sources
        assert "b" in sources

    def test_no_path(self) -> None:
        g = RestrictionGraph()
        g.add_edge("a", "b")
        assert not g.path_exists("a", "z")
