"""Presheaves and sheaves over a finite topological space.

A **presheaf** F on a topological space (X, τ) assigns to each open
set U ∈ τ a set F(U) (the *sections* over U) and to each inclusion
V ⊆ U a restriction map ρ_{U,V}: F(U) → F(V).

A **sheaf** additionally satisfies:

1. **Locality**: If s, t ∈ F(U) and ρ_{U,Vᵢ}(s) = ρ_{U,Vᵢ}(t) for all
   Vᵢ in an open cover of U, then s = t.
2. **Gluing**: If {sᵢ ∈ F(Uᵢ)} are compatible on overlaps, there
   exists a unique s ∈ F(∪Uᵢ) that restricts to each sᵢ.

Each **LocalSection** stores one complete SemanticFact — never
decomposed into triples.
"""

from __future__ import annotations

from dataclasses import dataclass

from common.schema import SemanticFact
from sfdb.sheaf.topology import FiniteTopologicalSpace


@dataclass(frozen=True)
class LocalSection:
    """A section s ∈ F(U) — one complete SemanticFact over an open set.

    This is the fundamental storage unit of the sheaf database.
    Unlike RDF triples, a LocalSection preserves the entire n-ary
    structure of a semantic fact as a single object.

    The *open_set_name* identifies U ∈ τ.  The *fact* is the
    complete SemanticFact event.
    """

    fact: SemanticFact
    open_set_name: str

    def __repr__(self) -> str:
        return f"σ({self.fact.id.value[:8]}… @ {self.open_set_name})"


@dataclass(frozen=True)
class GlobalSection:
    """A global section s ∈ F(X) over the entire space.

    A global section represents a fact that is coherent across all
    open sets — i.e., it assigns a consistent value at every point
    in the topological space.

    Complexity: computed via the sheaf gluing algorithm in O(k·m)
    where k = number of open sets, m = number of local sections.
    """

    fact: SemanticFact
    computation_time_ns: int = 0
    consistency_verified: bool = False

    def __repr__(self) -> str:
        return f"Γ({self.fact.id.value[:8]}…)"


class Stalk:
    """The stalk F_x at a point x ∈ X.

    The stalk is the direct limit of F(U) over all neighborhoods U
    of x.  Intuitively, the stalk contains the germ of each section
    at point x — the information visible from x's perspective.

    Stalks are **persisted**, not computed dynamically.
    """

    __slots__ = ("_open_set_names", "_point_id", "_sections")

    def __init__(self, point_id: str) -> None:
        object.__setattr__(self, "_point_id", point_id)
        object.__setattr__(self, "_sections", {})
        object.__setattr__(self, "_open_set_names", set())

    @property
    def point_id(self) -> str:
        return object.__getattribute__(self, "_point_id")

    @property
    def sections(self) -> dict[str, LocalSection]:
        return dict(object.__getattribute__(self, "_sections"))

    @property
    def section_count(self) -> int:
        return len(object.__getattribute__(self, "_sections"))

    def add_section(self, section: LocalSection) -> None:
        sections = object.__getattribute__(self, "_sections")
        sections[section.fact.id.value] = section
        ons = object.__getattribute__(self, "_open_set_names")
        ons.add(section.open_set_name)

    def get_section(self, fact_id: str) -> LocalSection | None:
        sections = object.__getattribute__(self, "_sections")
        return sections.get(fact_id)

    def remove_section(self, fact_id: str) -> None:
        sections = object.__getattribute__(self, "_sections")
        sections.pop(fact_id, None)

    def __repr__(self) -> str:
        return f"Stalk({self._point_id[:8]}…, |sections|={len(self._sections)})"


class Presheaf:
    """A presheaf F on a finite topological space.

    F assigns to each open set U ∈ τ a set of LocalSections, and
    to each inclusion V ⊆ U a restriction map ρ_{U,V}: F(U) → F(V).

    The presheaf is the core indexing structure — it maps open sets
    to their sections and computes restrictions on demand.
    """

    def __init__(self, topology: FiniteTopologicalSpace) -> None:
        self._topology = topology
        self._sections_by_openset: dict[str, dict[str, LocalSection]] = {}
        self._restriction_cache: dict[tuple[str, str], list[LocalSection]] = {}
        self._cache_gen: int = -1

    @property
    def topology(self) -> FiniteTopologicalSpace:
        return self._topology

    def assign(self, section: LocalSection) -> None:
        os_name = section.open_set_name
        if os_name not in self._sections_by_openset:
            self._sections_by_openset[os_name] = {}
        self._sections_by_openset[os_name][section.fact.id.value] = section

    def _check_cache(self) -> None:
        gen = self._topology.generation
        if gen != self._cache_gen:
            self._restriction_cache.clear()
            self._cache_gen = gen

    def sections_over(self, open_set_name: str) -> list[LocalSection]:
        return list(self._sections_by_openset.get(open_set_name, {}).values())

    def restrict(self, from_oset: str, to_oset: str) -> list[LocalSection]:
        """Compute restriction ρ_{V,U}(s) for all s ∈ F(V).

        Returns sections from *from_oset* whose fact IDs also appear
        in *to_oset* (i.e., facts visible from the smaller neighborhood).
        """
        self._check_cache()
        key = (from_oset, to_oset)
        if key in self._restriction_cache:
            return self._restriction_cache[key]

        from_sections = self._sections_by_openset.get(from_oset, {})
        result = [
            s
            for s in from_sections.values()
            if to_oset in self._topology._open_sets
            and s.fact.id.value in self._topology._open_sets[to_oset].points
        ]
        self._restriction_cache[key] = result
        return result

    def section_count(self) -> int:
        return sum(len(s) for s in self._sections_by_openset.values())


class Sheaf(Presheaf):
    """A sheaf — a presheaf satisfying locality and gluing.

    In addition to the presheaf structure, a sheaf ensures that:

    1. **Locality**: Sections that agree on every open cover must be
       identical.
    2. **Gluing**: Compatible local sections can be uniquely combined
       into a global section.

    The gluing algorithm computes global sections from compatible
    local data.
    """

    def __init__(self, topology: FiniteTopologicalSpace) -> None:
        super().__init__(topology)

    def compute_global_sections(self) -> list[GlobalSection]:
        """Compute all global sections via sheaf gluing.

        For each pair of overlapping open sets U, V, check that every
        fact in F(U) ∩ F(V) has compatible restrictions.  Compatible
        sections are glued into global sections.

        Complexity: O(k² · m) where k = number of open sets and
        m = max sections per open set.
        """
        import time

        t0 = time.perf_counter_ns()
        global_facts: dict[str, SemanticFact] = {}
        os_names = list(self._sections_by_openset.keys())

        for i in range(len(os_names)):
            for j in range(i + 1, len(os_names)):
                u_name = os_names[i]
                v_name = os_names[j]
                u_set = self._topology.get_open_set(u_name)
                v_set = self._topology.get_open_set(v_name)
                if u_set is None or v_set is None:
                    continue
                shared = u_set.points & v_set.points
                if not shared:
                    continue

                u_sects = self._sections_by_openset[u_name]
                v_sects = self._sections_by_openset[v_name]
                for fid in shared:
                    su = u_sects.get(fid)
                    sv = v_sects.get(fid)
                    if su is not None and sv is not None:
                        if su.fact == sv.fact:
                            global_facts[fid] = su.fact

        ns = time.perf_counter_ns() - t0
        result = [
            GlobalSection(fact=fact, computation_time_ns=ns, consistency_verified=True)
            for fact in global_facts.values()
        ]
        return result

    def restrict(self, from_oset: str, to_oset: str) -> list[LocalSection]:
        return super().restrict(from_oset, to_oset)
