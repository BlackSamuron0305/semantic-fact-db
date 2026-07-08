"""Restriction maps for the sheaf database.

In sheaf theory, a restriction map ρ_{V,U}: F(V) → F(U) is defined
whenever U ⊆ V (U is a smaller open set contained in V).  It maps
sections over the larger set V to sections over the smaller set U.

In this implementation, restriction maps filter local sections by
checking whether their fact IDs belong to the target open set.
This is semantically correct because:
- A fact visible from a larger neighborhood remains visible from any
  sub-neighborhood
- The section itself (the complete SemanticFact) is unchanged — only
  the open-set membership is restricted
"""

from __future__ import annotations

from dataclasses import dataclass

from common.types import Context


@dataclass(frozen=True)
class RestrictionMap:
    """An explicit restriction map ρ_{V,U}: F(V) → F(U).

    Attributes:
        source: The larger open set V
        target: The smaller open set U (U ⊆ V)
        computation_time_ns: Time to compute this restriction
        application_count: How many times this map has been applied
    """

    source_name: str
    target_name: str
    computation_time_ns: int = 0
    application_count: int = 0

    @property
    def key(self) -> tuple[str, str]:
        return (self.source_name, self.target_name)

    def __repr__(self) -> str:
        return f"ρ({self.source_name} → {self.target_name})"


@dataclass(frozen=True)
class ContextRestriction:
    """A restriction map specialised for context subsumption.

    When V and U are context-based open sets and c_U ≤ c_V in the
    context poset (U is a sub-context of V), this restriction maps
    sections from V to U, keeping only those facts whose context is
    compatible with U.
    """

    source_context: Context
    target_context: Context
    is_valid: bool = True

    def __repr__(self) -> str:
        return f"ρ_ctx({self.source_context} → {self.target_context})"


@dataclass(frozen=True)
class TemporalRestriction:
    """A restriction map specialised for temporal filtering.

    Restricts facts to those whose temporal validity interval overlaps
    the target time window.
    """

    source_start: str
    source_end: str
    target_start: str
    target_end: str

    def __repr__(self) -> str:
        return f"ρ_time([{self.source_start}, {self.source_end}] → [{self.target_start}, {self.target_end}])"


class RestrictionGraph:
    """A directed acyclic graph of restriction maps.

    Nodes are open set names.  An edge ρ: V → U exists iff U ⊆ V
    (U is a sub-neighborhood of V).

    The restriction graph is used by the query planner to find
    optimal restriction paths.
    """

    def __init__(self) -> None:
        self._edges: dict[str, set[str]] = {}

    def add_edge(self, source: str, target: str) -> None:
        if source not in self._edges:
            self._edges[source] = set()
        self._edges[source].add(target)

    def get_targets(self, source: str) -> frozenset[str]:
        return frozenset(self._edges.get(source, set()))

    def get_sources(self, target: str) -> list[str]:
        return [src for src, tgts in self._edges.items() if target in tgts]

    def path_exists(self, source: str, target: str) -> bool:
        """Check if a restriction path exists from *source* to *target*."""
        visited: set[str] = set()
        stack = [source]
        while stack:
            node = stack.pop()
            if node == target:
                return True
            if node in visited:
                continue
            visited.add(node)
            for tgt in self._edges.get(node, set()):
                stack.append(tgt)
        return False

    def edge_count(self) -> int:
        return sum(len(tgts) for tgts in self._edges.values())

    def node_count(self) -> int:
        return len(self._edges)

    def __repr__(self) -> str:
        return f"RestrictionGraph(|V|={self.node_count()}, |E|={self.edge_count()})"
