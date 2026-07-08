"""Visualization utilities for the sheaf database.

Generates DOT-format graph descriptions for:
- Finite topology (open sets and inclusion relationships)
- Restriction graph (restriction maps as directed edges)
- Stalk relationships (points and their stalks)
- Global section construction (gluing process)
- Open set contents (fact membership)
"""

from __future__ import annotations

from sfdb.sheaf.presheaf import GlobalSection, Presheaf
from sfdb.sheaf.restriction import RestrictionGraph
from sfdb.sheaf.topology import FiniteTopologicalSpace


class SheafViz:
    """Visualization utilities for the sheaf database.

    All methods return DOT-format graph strings that can be rendered
    with Graphviz (``dot``, ``neato``).
    """

    @staticmethod
    def render_topology(topology: FiniteTopologicalSpace, max_sets: int = 20) -> str:
        """Render the finite topology as a Hasse diagram of open sets.

        Edges go from larger sets (coarser) to smaller sets (finer).
        """
        lines = [
            "digraph Topology {",
            "  rankdir=BT;",
            "  node [shape=box, style=filled, fillcolor=lightyellow];",
        ]
        os_list = list(topology._open_sets.values())[:max_sets]
        for os_ in os_list:
            label = f"{os_.name}\\n|points|={len(os_.points)}"
            safe_name = os_.name.replace(":", "_").replace(".", "_")
            lines.append(f'  {safe_name} [label="{label}"];')
        for os_ in os_list:
            for other in os_list:
                if (
                    os_.name != other.name
                    and os_.is_subset_of(other)
                    and len(os_.points) < len(other.points)
                ):
                    safe_child = os_.name.replace(":", "_").replace(".", "_")
                    safe_parent = other.name.replace(":", "_").replace(".", "_")
                    lines.append(f"  {safe_child} -> {safe_parent};")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def render_restriction_graph(graph: RestrictionGraph, max_nodes: int = 20) -> str:
        """Render restriction maps as a directed graph."""
        lines = [
            "digraph Restriction {",
            "  rankdir=LR;",
            "  node [shape=ellipse, style=filled, fillcolor=lightblue];",
        ]
        nodes = set(graph._edges.keys())
        for t in graph._edges.values():
            nodes.update(t)
        nodes = list(nodes)[:max_nodes]
        for n in nodes:
            safe = n.replace(":", "_").replace(".", "_")
            lines.append(f'  {safe} [label="{n}"];')
        for src, tgts in list(graph._edges.items())[:max_nodes]:
            safe_src = src.replace(":", "_").replace(".", "_")
            for tgt in tgts:
                safe_tgt = tgt.replace(":", "_").replace(".", "_")
                if safe_src in [
                    x.replace(":", "_").replace(".", "_") for x in nodes
                ] and safe_tgt in [x.replace(":", "_").replace(".", "_") for x in nodes]:
                    lines.append(f"  {safe_src} -> {safe_tgt};")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def render_stalks(presheaf: Presheaf, max_stalks: int = 10) -> str:
        """Render stalks and their sections."""
        lines = [
            "digraph Stalks {",
            "  rankdir=LR;",
            "  node [shape=record, style=filled, fillcolor=lightgreen];",
        ]
        os_names = list(presheaf._sections_by_openset.keys())[:max_stalks]
        for i, os_name in enumerate(os_names):
            sections = presheaf.sections_over(os_name)
            label = f"{{ {os_name} | {len(sections)} sections }}"
            safe = f"os_{i}"
            lines.append(f'  {safe} [label="{label}"];')
        if len(os_names) >= 2:
            for i in range(len(os_names) - 1):
                lines.append(f"  os_{i} -> os_{i + 1} [style=dashed, label='restrict'];")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def render_global_sections(sections: list[GlobalSection], max_sections: int = 15) -> str:
        """Render global sections."""
        lines = [
            "digraph GlobalSections {",
            "  rankdir=TB;",
            "  node [shape=box, style=filled, fillcolor=lightcyan];",
        ]
        for i, gs in enumerate(sections[:max_sections]):
            fid = gs.fact.id.value[:8]
            label = f"Γ({fid})\\nrelation={gs.fact.relation.value}\\nverified={gs.consistency_verified}"
            lines.append(f'  gs_{i} [label="{label}"];')
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def render_open_set_contents(
        topology: FiniteTopologicalSpace,
        open_set_name: str,
    ) -> str:
        """Render the contents of a single open set."""
        os_ = topology.get_open_set(open_set_name)
        if os_ is None:
            return f"// Open set '{open_set_name}' not found"
        lines = [
            "digraph OpenSet {",
            "  rankdir=LR;",
            "  node [shape=circle, style=filled, fillcolor=lightyellow];",
        ]
        for pt in os_.points:
            safe = pt[:8].replace(":", "_")
            lines.append(f'  "{safe}" [label="{pt[:8]}"];')
        lines.append("}")
        return "\n".join(lines)
