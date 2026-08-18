"""Regression test: the restriction graph must not retain stale edges.

`_build_restriction_edges` only ever calls `RestrictionGraph.add_edge`;
without an explicit `clear()` before rebuilding, an edge recorded before
an insert broke its underlying subset relationship would survive
forever, since the graph has no other way to shrink. This directly
constructs the scenario: build once, insert a fact that breaks a
previously-true subset relationship, rebuild, and assert the broken
edge is gone.
"""

from __future__ import annotations

from datetime import UTC, datetime

from common.schema import SemanticFact
from common.types import Context, Identifier, TemporalInfo, Value
from sfdb.sheaf.engine import SheafDatabaseEngine
from sfdb.sheaf.restriction import RestrictionGraph
from sfdb.sheaf.topology import FiniteTopologicalSpace, OpenSet


def test_restriction_graph_clear_removes_prior_edges() -> None:
    graph = RestrictionGraph()
    graph.add_edge("A", "B")
    graph.add_edge("A", "C")
    assert graph.get_targets("A") == frozenset({"B", "C"})

    graph.clear()

    assert graph.get_targets("A") == frozenset()


def test_engine_drops_stale_edge_after_insert_breaks_subset() -> None:
    """entity:e is a subset of temporal:atemporal until a temporal fact
    mentioning e is inserted, at which point it must no longer be."""
    engine = SheafDatabaseEngine(name="test_stale_edge")
    engine.create()

    atemporal_fact = SemanticFact(
        id=Identifier("f1"),
        subject=Identifier("e"),
        relation=Identifier("r"),
        objects=(Value.literal("x"),),
        context=Context("world"),
    )
    engine.insert(atemporal_fact)
    engine._build_restriction_edges()

    # Before the second insert, every fact touching entity "e" is
    # atemporal, so entity:e ⊆ temporal:atemporal.
    assert "entity:e" in engine._restriction_graph.get_targets("temporal:atemporal")

    temporal_fact = SemanticFact(
        id=Identifier("f2"),
        subject=Identifier("e"),
        relation=Identifier("r"),
        objects=(Value.literal("y"),),
        context=Context("world"),
        temporal=TemporalInfo(start=datetime(2024, 1, 1, tzinfo=UTC)),
    )
    engine.insert(temporal_fact)
    engine._build_restriction_edges()

    # entity:e now also contains a fact outside temporal:atemporal, so
    # the subset relationship is broken and the edge must be gone.
    assert "entity:e" not in engine._restriction_graph.get_targets("temporal:atemporal"), (
        "stale restriction-graph edge survived a topology change that broke it"
    )


def test_topology_open_sets_containing() -> None:
    topo = FiniteTopologicalSpace()
    topo.add_open_set(OpenSet("A", frozenset({"p1", "p2"})))
    topo.add_open_set(OpenSet("B", frozenset({"p1"})))

    assert topo.open_sets_containing("p1") == {"A", "B"}
    assert topo.open_sets_containing("p2") == {"A"}
    assert topo.open_sets_containing("nonexistent") == set()
