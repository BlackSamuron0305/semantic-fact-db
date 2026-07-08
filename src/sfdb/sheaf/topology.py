"""Finite topological spaces for the sheaf database.

Provides the mathematical foundation: a finite topological space is a
pair (X, τ) where X is a finite set of points (semantic fact IDs) and
τ is a collection of open subsets closed under finite intersection and
arbitrary union.

Each open set represents a semantic neighborhood — facts that share
some common property (entity, event, temporal interval, provenance
source, context).
"""

from __future__ import annotations

from typing import Any


class OpenSet:
    """An open set in a finite topological space.

    Each open set is identified by a unique name and contains a
    collection of point IDs (SemanticFact identifiers).

    The open set is the fundamental unit of the topology — it groups
    facts that are ``close'' according to some semantic criterion.
    """

    __slots__ = ("_metadata", "_name", "_points")

    def __init__(
        self,
        name: str,
        points: frozenset[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_points", points if points is not None else frozenset())
        object.__setattr__(self, "_metadata", metadata if metadata is not None else {})

    @property
    def name(self) -> str:
        return object.__getattribute__(self, "_name")

    @property
    def points(self) -> frozenset[str]:
        return object.__getattribute__(self, "_points")

    @property
    def metadata(self) -> dict[str, Any]:
        return object.__getattribute__(self, "_metadata")

    def contains(self, point_id: str) -> bool:
        return point_id in self._points

    def is_subset_of(self, other: OpenSet) -> bool:
        return self._points.issubset(other._points)

    def intersect(self, other: OpenSet) -> OpenSet:
        new_points = self._points & other._points
        new_name = f"{self._name}∩{other._name}"
        return OpenSet(new_name, new_points)

    def union(self, other: OpenSet) -> OpenSet:
        new_points = self._points | other._points
        new_name = f"{self._name}∪{other._name}"
        return OpenSet(new_name, new_points)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OpenSet):
            return NotImplemented
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)

    def __repr__(self) -> str:
        return f"Ω({self._name}, |points|={len(self._points)})"

    def __le__(self, other: OpenSet) -> bool:
        """U ≤ V iff U is a subset of V (U is finer)."""
        return self._points.issubset(other._points)


class Neighborhood:
    """A neighborhood of a point — an open set containing that point.

    In a finite topological space, a neighborhood of x ∈ X is any open
    set U ∈ τ such that x ∈ U.
    """

    __slots__ = ("_center", "_open_set")

    def __init__(self, center: str, open_set: OpenSet) -> None:
        object.__setattr__(self, "_center", center)
        object.__setattr__(self, "_open_set", open_set)

    @property
    def center(self) -> str:
        return object.__getattribute__(self, "_center")

    @property
    def open_set(self) -> OpenSet:
        return object.__getattribute__(self, "_open_set")

    def __repr__(self) -> str:
        return f"𝒩({self._center}) ∈ {self._open_set.name}"


class FiniteTopologicalSpace:
    """A finite topological space (X, τ).

    X is a finite set of point IDs.  τ is a collection of open subsets
    satisfying:

    1. ∅ ∈ τ and X ∈ τ
    2. U, V ∈ τ ⇒ U ∩ V ∈ τ (finite intersection)
    3. {Uᵢ} ⊆ τ ⇒ ∪Uᵢ ∈ τ (arbitrary union)

    In a finite space, the topology is completely determined by the
    minimal open sets (the specialization preorder).  We store the full
    lattice for direct access.

    Complexity
    ----------
    - Membership: O(|τ|)
    - Intersection closure: O(|τ|²)
    - Neighborhood query: O(|τ|)
    """

    def __init__(self) -> None:
        self._name: str = "sheaf_topology"
        self._open_sets: dict[str, OpenSet] = {}
        self._point_to_opensets: dict[str, set[str]] = {}
        self._generation: int = 0
        self._dirty_restriction: bool = True

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def open_sets(self) -> dict[str, OpenSet]:
        return dict(self._open_sets)

    @property
    def points(self) -> frozenset[str]:
        return frozenset(self._point_to_opensets.keys())

    def add_open_set(self, open_set: OpenSet) -> None:
        self._open_sets[open_set.name] = open_set
        for pt in open_set.points:
            self._point_to_opensets.setdefault(pt, set()).add(open_set.name)
        self._generation += 1
        self._dirty_restriction = True

    def add_point_to_open_set(self, open_set_name: str, point_id: str) -> None:
        """Add a point to an existing open set (incremental topology update).

        Avoids rebuilding the entire topology when inserting a single fact.
        """
        existing = self._open_sets.get(open_set_name)
        if existing is not None:
            new_points = existing.points | {point_id}
            updated = OpenSet(
                name=existing.name,
                points=frozenset(new_points),
                metadata=dict(existing.metadata),
            )
            self._open_sets[open_set_name] = updated
        else:
            new_os = OpenSet(
                name=open_set_name,
                points=frozenset({point_id}),
            )
            self._open_sets[open_set_name] = new_os
        self._point_to_opensets.setdefault(point_id, set()).add(open_set_name)
        self._generation += 1
        self._dirty_restriction = True

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def is_restriction_dirty(self) -> bool:
        return self._dirty_restriction

    def mark_restriction_clean(self) -> None:
        self._dirty_restriction = False

    def remove_open_set(self, name: str) -> None:
        os = self._open_sets.pop(name, None)
        if os is not None:
            for pt in os.points:
                if pt in self._point_to_opensets:
                    self._point_to_opensets[pt].discard(name)
                    if not self._point_to_opensets[pt]:
                        del self._point_to_opensets[pt]

    def get_open_set(self, name: str) -> OpenSet | None:
        return self._open_sets.get(name)

    def contains_open_set(self, name: str) -> bool:
        return name in self._open_sets

    def neighborhoods(self, point_id: str) -> list[Neighborhood]:
        result: list[Neighborhood] = []
        for os_name in self._point_to_opensets.get(point_id, set()):
            os = self._open_sets[os_name]
            result.append(Neighborhood(point_id, os))
        return result

    def minimal_open_set(self, point_id: str) -> OpenSet | None:
        """Return the smallest open set containing *point_id*."""
        nbs = self.neighborhoods(point_id)
        if not nbs:
            return None
        smallest = min(nbs, key=lambda n: len(n.open_set.points))
        return smallest.open_set

    def intersection_closure(self) -> None:
        """Ensure τ is closed under finite intersection."""
        changed = True
        while changed:
            changed = False
            names = list(self._open_sets.keys())
            existing_point_sets = {os.points for os in self._open_sets.values()}
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    u = self._open_sets[names[i]]
                    v = self._open_sets[names[j]]
                    inter = u.intersect(v)
                    if inter.points not in existing_point_sets and inter.points:
                        self.add_open_set(inter)
                        existing_point_sets.add(inter.points)
                        changed = True

    def open_set_count(self) -> int:
        return len(self._open_sets)

    def point_count(self) -> int:
        return len(self._point_to_opensets)

    def __repr__(self) -> str:
        return f"𝕏({self._name}, |X|={self.point_count()}, |τ|={self.open_set_count()})"
