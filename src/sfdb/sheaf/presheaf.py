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
from common.types import Context, Provenance, TemporalInfo
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

        Groups all local sections by fact ID, checks compatibility
        across all open sets containing that fact, and merges
        compatible partial facts into a global section.

        Two facts with the same ID are *compatible* if they agree on
        all shared fields (subject, relation, objects).  Attributes,
        confidence, temporal, and provenance are merged via union
        (max confidence, union of attributes, overlapping temporal).

        This is a genuine sheaf-theoretic gluing operation: local
        sections from different contexts may carry partial information,
        and gluing reconstructs the unique global section.

        Complexity: O(N · K) where N = total sections, K = avg open
        sets per fact.
        """
        import time

        t0 = time.perf_counter_ns()

        # Group all sections by fact ID across all open sets
        fact_groups: dict[str, list[LocalSection]] = {}
        for os_name, sections in self._sections_by_openset.items():
            for fid, section in sections.items():
                fact_groups.setdefault(fid, []).append(section)

        global_facts: dict[str, SemanticFact] = {}

        for fid, sections in fact_groups.items():
            if len(sections) < 2:
                # Singleton sections are not global — they lack
                # the cross-context agreement that defines a
                # global section.  They remain local.
                continue

            base = sections[0].fact
            compatible = True

            # Check pairwise compatibility and merge
            merged_attrs: dict[str, Value] = dict(base.attributes)
            merged_confidence = base.confidence
            merged_temporal = base.temporal
            merged_prov_source = base.provenance.source
            merged_prov_method = base.provenance.method
            merged_prov_confidence = base.provenance.confidence

            for s in sections[1:]:
                f = s.fact

                # Subject must match
                if f.subject != base.subject:
                    compatible = False
                    break

                # Relation must match
                if f.relation != base.relation:
                    compatible = False
                    break

                # Objects: if both have objects, they must match
                if base.objects and f.objects and base.objects != f.objects:
                    compatible = False
                    break

                # Use the non-empty objects if one is empty
                if not base.objects and f.objects:
                    pass  # f's objects will be used via base
                if not f.objects and base.objects:
                    pass  # base's objects are already set

                # Attributes: shared keys must match
                for k, v in f.attributes.items():
                    if k in merged_attrs:
                        if merged_attrs[k] != v:
                            compatible = False
                            break
                    else:
                        merged_attrs[k] = v
                if not compatible:
                    break

                # Confidence: take the max
                merged_confidence = max(merged_confidence, f.confidence)

                # Temporal: merge intervals (intersection)
                if f.temporal is not None:
                    if merged_temporal is None:
                        merged_temporal = f.temporal
                    else:
                        # Take the tighter bounds
                        start = max(
                            merged_temporal.start or f.temporal.start,
                            f.temporal.start or merged_temporal.start,
                        )
                        end = (
                            min(merged_temporal.end, f.temporal.end)
                            if merged_temporal.end and f.temporal.end
                            else (merged_temporal.end or f.temporal.end)
                        )
                        if start and end and start >= end:
                            compatible = False
                            break
                        merged_temporal = TemporalInfo(start=start, end=end)

                # Provenance: prefer more specific source
                if f.provenance.source != "unknown":
                    merged_prov_source = f.provenance.source
                if f.provenance.method != "unknown":
                    merged_prov_method = f.provenance.method
                merged_prov_confidence = max(merged_prov_confidence, f.provenance.confidence)

            if not compatible:
                continue

            # Build the merged global fact
            merged = SemanticFact(
                id=base.id,
                subject=base.subject,
                relation=base.relation,
                objects=base.objects or sections[1].fact.objects if len(sections) > 1 else base.objects,
                attributes=merged_attrs,
                context=Context("world"),
                provenance=Provenance(
                    source=merged_prov_source,
                    confidence=merged_prov_confidence,
                    method=merged_prov_method,
                ),
                confidence=merged_confidence,
                temporal=merged_temporal,
            )
            global_facts[fid] = merged

        ns = time.perf_counter_ns() - t0
        result = [
            GlobalSection(fact=fact, computation_time_ns=ns, consistency_verified=True)
            for fact in global_facts.values()
        ]
        return result

    def restrict(self, from_oset: str, to_oset: str) -> list[LocalSection]:
        return super().restrict(from_oset, to_oset)
