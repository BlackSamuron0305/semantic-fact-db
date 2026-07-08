"""Tests for graph visualization utilities."""

from __future__ import annotations

from sfdb.kg.visualization import GraphvizRenderer, KGViz


class TestGraphvizRenderer:
    def test_empty_render(self) -> None:
        renderer = GraphvizRenderer("Test")
        output = renderer.render()
        assert "digraph Test" in output
        assert "rankdir=LR" in output

    def test_add_node(self) -> None:
        renderer = GraphvizRenderer()
        renderer.add_node("n1", "Node 1")
        output = renderer.render()
        assert "n1" in output
        assert '"Node 1"' in output

    def test_add_edge(self) -> None:
        renderer = GraphvizRenderer()
        renderer.add_node("a", "A")
        renderer.add_node("b", "B")
        renderer.add_edge("a", "b", "edge_label")
        output = renderer.render()
        assert '"a" -> "b"' in output
        assert "edge_label" in output

    def test_add_subgraph(self) -> None:
        renderer = GraphvizRenderer()
        renderer.add_subgraph("sg1", "Subgraph 1", ["n1", "n2"])
        output = renderer.render()
        assert "cluster_sg1" in output
        assert "Subgraph 1" in output

    def test_clear(self) -> None:
        renderer = GraphvizRenderer()
        renderer.add_node("n1", "Node 1")
        renderer.clear()
        output = renderer.render()
        assert "n1" not in output


class TestKGViz:
    def test_entity_graph(self) -> None:
        triples = [(1, 10, 2, "entity", 0, "subject")]
        viz = KGViz(triples)
        output = viz.entity_graph()
        assert "EntityGraph" in output
        assert "E1" in output or "Entity 1" in output

    def test_event_graph(self) -> None:
        triples = [(1, 10, 2, "entity", 100, "agent")]
        viz = KGViz(triples)
        output = viz.event_graph()
        assert "EventGraph" in output
        assert "EV100" in output

    def test_neighborhood_graph(self) -> None:
        triples = [(1, 10, 2, "entity", 0, "subject")]
        viz = KGViz(triples)
        output = viz.neighborhood_graph(entity_id=1)
        assert "Neighborhood_1" in output
