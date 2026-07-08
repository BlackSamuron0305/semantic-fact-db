"""Graph visualization utilities for the Knowledge Graph.

Provides:
  - Entity graph: show entities connected by relations
  - Predicate graph: show predicate distribution
  - Event graph: show event nodes and their decomposition
  - Neighborhood graph: show subgraph around an entity

Outputs Graphviz DOT format and optionally renders images.
"""

from __future__ import annotations


class GraphvizRenderer:
    """Generates Graphviz DOT language output from KG data."""

    def __init__(self, name: str = "KG") -> None:
        self._name = name
        self._nodes: list[str] = []
        self._edges: list[str] = []
        self._subgraphs: list[str] = []

    def add_node(self, node_id: str, label: str, **attrs: str) -> None:
        attr_str = self._format_attrs(attrs)
        self._nodes.append(f'  "{node_id}" [label="{label}"{attr_str}];')

    def add_edge(self, src: str, dst: str, label: str = "", **attrs: str) -> None:
        attr_str = self._format_attrs(attrs)
        label_part = f' label="{label}"' if label else ""
        self._edges.append(f'  "{src}" -> "{dst}" [{label_part}{attr_str}];')

    def add_subgraph(self, name: str, label: str, nodes: list[str]) -> None:
        node_lines = "\n".join(f'    "{n}";' for n in nodes)
        self._subgraphs.append(
            f'  subgraph "cluster_{name}" {{\n    label="{label}";\n{node_lines}\n  }}'
        )

    def render(self, rankdir: str = "LR") -> str:
        lines = [
            f"digraph {self._name} {{",
            f"  rankdir={rankdir};",
            "  node [shape=box, style=rounded, fontname=monospace];",
            "  edge [fontname=monospace, fontsize=10];",
            *self._nodes,
            *self._edges,
            *self._subgraphs,
            "}",
        ]
        return "\n".join(lines)

    def clear(self) -> None:
        self._nodes.clear()
        self._edges.clear()
        self._subgraphs.clear()

    @staticmethod
    def _format_attrs(attrs: dict[str, str]) -> str:
        if not attrs:
            return ""
        parts = [f'{k}="{v}"' for k, v in attrs.items()]
        return ", " + ", ".join(parts)


class KGViz:
    """High-level visualization builder for Knowledge Graph data."""

    def __init__(self, triples: list[tuple]) -> None:
        self._triples = triples
        self._renderer = GraphvizRenderer()

    def entity_graph(self) -> str:
        """Show entities (subjects, objects) connected by predicates."""
        self._renderer.clear()
        self._renderer = GraphvizRenderer("EntityGraph")
        seen_entities: set[str] = set()
        for t in self._triples:
            subj_id, pred_id, obj_id, obj_type, *_ = t
            subj_str = f"E{subj_id}"
            if subj_str not in seen_entities:
                self._renderer.add_node(subj_str, f"Entity {subj_id}", shape="ellipse")
                seen_entities.add(subj_str)
            if obj_type == "entity":
                obj_str = f"E{obj_id}"
                if obj_str not in seen_entities:
                    self._renderer.add_node(obj_str, f"Entity {obj_id}", shape="ellipse")
                    seen_entities.add(obj_str)
                self._renderer.add_edge(subj_str, obj_str, f"P{pred_id}")
        return self._renderer.render()

    def predicate_graph(self) -> str:
        """Show predicate distribution as a bar-like graph."""
        self._renderer.clear()
        self._renderer = GraphvizRenderer("PredicateGraph")
        pred_counts: dict[int, int] = {}
        for t in self._triples:
            pred_id = t[1]
            pred_counts[pred_id] = pred_counts.get(pred_id, 0) + 1
        for pid, count in pred_counts.items():
            self._renderer.add_node(f"P{pid}", f"Pred {pid} ({count})", shape="box")
        for t in self._triples:
            _subj_id, pred_id, _obj_id, _obj_type, *_ = t
            if pid == pred_id:
                continue
        return self._renderer.render()

    def event_graph(self, event_id: int | None = None) -> str:
        """Show event nodes and their decomposition triples."""
        self._renderer.clear()
        self._renderer = GraphvizRenderer("EventGraph")
        events: dict[int, list[tuple]] = {}
        for t in self._triples:
            ev_id = t[4]
            if event_id is not None and ev_id != event_id:
                continue
            events.setdefault(ev_id, []).append(t)

        for ev_id, triples in events.items():
            ev_str = f"EV{ev_id}"
            self._renderer.add_node(
                ev_str, f"Event {ev_id}", shape="diamond", style="filled", fillcolor="lightyellow"
            )
            ev_nodes: list[str] = [ev_str]
            for t in triples:
                pred_id, obj_id, obj_type, role = t[1], t[2], t[3], t[5]
                node_id = f"{ev_str}_{pred_id}"
                self._renderer.add_node(node_id, f"{role}\\n(P{pred_id}: O{obj_id})", shape="note")
                self._renderer.add_edge(ev_str, node_id, role)
                if obj_type == "entity":
                    ent_str = f"E{obj_id}"
                    if ent_str not in [ev_str]:
                        seen = any(ent_str in line for line in self._renderer._nodes)
                        if not seen:
                            self._renderer.add_node(ent_str, f"Entity {obj_id}", shape="ellipse")
                    self._renderer.add_edge(node_id, ent_str, "refers")
                ev_nodes.append(node_id)
            self._add_subgraph_safe(f"event_{ev_id}", f"Event {ev_id}", ev_nodes)

        return self._renderer.render()

    def neighborhood_graph(self, entity_id: int, depth: int = 1) -> str:
        """Show the subgraph around an entity (BFS up to depth)."""
        self._renderer.clear()
        self._renderer = GraphvizRenderer(f"Neighborhood_{entity_id}")
        visited: set[int] = {entity_id}
        current: set[int] = {entity_id}

        ent_str = f"E{entity_id}"
        self._renderer.add_node(
            ent_str, f"Entity {entity_id}", shape="ellipse", style="filled", fillcolor="lightblue"
        )

        for _ in range(depth):
            next_set: set[int] = set()
            for t in self._triples:
                subj_id, pred_id, obj_id, obj_type, _ev_id, _role = (
                    t[0],
                    t[1],
                    t[2],
                    t[3],
                    t[4],
                    t[5],
                )
                if subj_id in current:
                    obj_str = f"E{obj_id}" if obj_type == "entity" else f"L{obj_id}"
                    subj_str = f"E{subj_id}"
                    if obj_id not in visited and obj_type == "entity":
                        next_set.add(obj_id)
                        self._renderer.add_node(obj_str, f"Entity {obj_id}", shape="ellipse")
                    elif obj_type == "literal":
                        name = f"L{obj_id}"
                        if name not in visited:
                            self._renderer.add_node(name, f"Literal {obj_id}", shape="box")
                    visited.add(obj_id)
                    self._renderer.add_edge(
                        subj_str, obj_str if obj_type == "entity" else f"L{obj_id}", f"P{pred_id}"
                    )
                if obj_id in current and obj_type == "entity":
                    subj_str = f"E{subj_id}"
                    obj_str = f"E{obj_id}"
                    if subj_id not in visited:
                        next_set.add(subj_id)
                        self._renderer.add_node(subj_str, f"Entity {subj_id}", shape="ellipse")
                    visited.add(subj_id)
                    self._renderer.add_edge(subj_str, obj_str, f"P{pred_id}")
            current = next_set
            if not current:
                break
        return self._renderer.render()

    def _add_subgraph_safe(self, name: str, label: str, nodes: list[str]) -> None:
        node_ids = [n.split('"')[1] if '"' in n else n for n in nodes]
        self._renderer.add_subgraph(name, label, node_ids)
