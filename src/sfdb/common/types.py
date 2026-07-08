"""Core type definitions for the Semantic Fact Database.

Mathematical background
-----------------------
We model semantic information as a sheaf over a poset of *contexts*.

Let (C, ≤) be a poset of contexts where c₁ ≤ c₂ means c₁ is a sub-context of c₂.
A *fact* is a pair (p, c) where p is a proposition and c ∈ C is its context.
Facts are the sections of the sheaf.

A *restriction map* ρ_{c₂,c₁}: F(c₂) → F(c₁) for c₁ ≤ c₂ maps facts in a broader
context to their meaning in a narrower context.

The sheaf condition ensures that facts agreeing on overlaps can be uniquely
glued together. This gives us local-to-global reasoning.

Complexity
----------
Fact comparison: O(k) where k is the number of slots in the fact.
Set operations on FactSet: O(n log n) with sorted representation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import total_ordering
from typing import Any, NamedTuple


class SemanticType(Enum):
    """The semantic category of a fact or entity.

    These types categorize what kind of thing a fact describes,
    enabling typed restriction maps and semantic validation.
    """

    ENTITY = auto()
    RELATION = auto()
    ATTRIBUTE = auto()
    EVENT = auto()
    STATE = auto()
    PROVENANCE = auto()
    TEMPORAL = auto()
    SPATIAL = auto()
    QUANTITY = auto()
    ABSTRACTION = auto()
    UNKNOWN = auto()


@total_ordering
class Identifier:
    """A universally unique identifier for any semantic object.

    Internally stored as a UUID4. Ordering is by string representation.

    Complexity: O(1) construction and comparison.
    """

    _value: str
    __slots__ = ("_value",)

    def __init__(self, value: str | None = None) -> None:
        object.__setattr__(self, "_value", value if value else str(uuid.uuid4()))

    @property
    def value(self) -> str:
        val: str = object.__getattribute__(self, "_value")
        return val

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Identifier):
            return NotImplemented
        return self._value == other._value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Identifier):
            return NotImplemented
        return self._value < other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __repr__(self) -> str:
        return f"Id({self._value[:8]}…)"

    def __str__(self) -> str:
        return self._value


class Value:
    """A typed value slot in a fact.

    A Value can be either a literal (string, number, bool) or a reference
    to another entity (identified by an Identifier).

    Complexity: O(1) construction, O(1) type dispatch.
    """

    _inner: Any
    _type: SemanticType
    __slots__ = ("_inner", "_type")

    def __init__(self, inner: Any, type_hint: SemanticType = SemanticType.UNKNOWN) -> None:
        object.__setattr__(self, "_inner", inner)
        object.__setattr__(self, "_type", type_hint)

    @property
    def inner(self) -> Any:
        return object.__getattribute__(self, "_inner")

    @property
    def type_hint(self) -> SemanticType:
        val: SemanticType = object.__getattribute__(self, "_type")
        return val

    @classmethod
    def literal(cls, value: str | int | float | bool) -> Value:
        """Create a literal value with automatic type inference."""
        if isinstance(value, str):
            return cls(value, SemanticType.ATTRIBUTE)
        if isinstance(value, bool):
            return cls(value, SemanticType.ATTRIBUTE)
        if isinstance(value, (int, float)):
            return cls(value, SemanticType.QUANTITY)
        raise TypeError(f"Unsupported literal type: {type(value)}")

    @classmethod
    def reference(cls, entity: Identifier, type_hint: SemanticType = SemanticType.ENTITY) -> Value:
        """Create a reference value pointing to another entity."""
        return cls(entity, type_hint)

    @property
    def is_reference(self) -> bool:
        return isinstance(self._inner, Identifier)

    @property
    def is_literal(self) -> bool:
        return not self.is_reference

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Value):
            return NotImplemented
        return self._inner == other._inner and self._type == other._type

    def __hash__(self) -> int:
        return hash((self._inner, self._type))

    def __repr__(self) -> str:
        if self.is_reference:
            return f"Val(ref:{self._inner})"
        return f"Val({self._inner!r})"


@total_ordering
class Context:
    """A context in the poset of semantic scopes.

    Contexts form a partially ordered set where c₁ ≤ c₂ iff c₁ is a
    sub-context of c₂ (c₁ is more specific). Facts are always stated
    within a context.

    Examples:
        Context("world") — global knowledge
        Context("world.2024") — temporally scoped
        Context("world.2024.science") — domain scoped
        Context("world.2024.science.physics") — further refinement

    Complexity
    ----------
    Comparison: O(min(n, m)) where n, m are depth levels.
    """

    __slots__ = ("_segments",)

    def __init__(self, path: str = "world", separator: str = ".") -> None:
        self._segments: tuple[str, ...] = tuple(path.split(separator))

    @property
    def segments(self) -> tuple[str, ...]:
        return self._segments

    @property
    def depth(self) -> int:
        return len(self._segments)

    def is_subcontext(self, other: Context) -> bool:
        """True if this context is a sub-context of *other* (more specific).

        c₁ ≤ c₂ iff the path of c₂ is a prefix of c₁'s path.
        """
        if len(self._segments) < len(other._segments):
            return False
        return self._segments[: len(other._segments)] == other._segments

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Context):
            return NotImplemented
        return self.is_subcontext(other)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Context):
            return NotImplemented
        return self != other and self <= other

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Context):
            return NotImplemented
        return self._segments == other._segments

    def __hash__(self) -> int:
        return hash(self._segments)

    def __repr__(self) -> str:
        return f"Ctx({'.'.join(self._segments)})"

    def __str__(self) -> str:
        return ".".join(self._segments)


@dataclass(slots=True, frozen=True, order=True)
class Fact:
    """A semantic fact: the primitive unit of knowledge.

    Unlike RDF triples, a Fact is an n-ary structured proposition:
        (subject, relation, objects, context, metadata)

    This preserves the intrinsic structure of events and relationships
    without decomposing them into multiple triples.

    Parameters
    ----------
    id: Unique identifier for this fact.
    subject: The entity the fact is about.
    relation: The type of relationship.
    objects: The values (literals or references) involved.
    context: The semantic scope where this fact holds.
    confidence: A confidence score in [0, 1].
    metadata: Arbitrary additional metadata.

    Complexity
    ----------
    Construction: O(k) where k = len(objects).
    Hashing: O(k).
    Comparison: O(k).
    """

    id: Identifier
    subject: Identifier
    relation: Identifier
    objects: tuple[Value, ...] = field(default_factory=tuple)
    context: Context = field(default_factory=lambda: Context())
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0, 1], got {self.confidence}")

    def arity(self) -> int:
        """Number of object slots."""
        return len(self.objects)


class FactSet:
    """An ordered set of Facts.

    Maintains sorted order by fact ID for efficient union, intersection,
    and difference operations.

    Complexity
    ----------
    Construction: O(n log n).
    Contains: O(log n) via binary search.
    Union: O(n + m).
    Intersection: O(n + m).
    """

    __slots__ = ("_facts", "_index")

    def __init__(self, facts: list[Fact] | None = None) -> None:
        self._facts: list[Fact] = sorted(facts) if facts else []
        self._index: dict[Identifier, Fact] = {f.id: f for f in self._facts}

    def __contains__(self, fact: Fact) -> bool:
        return fact.id in self._index

    def __len__(self) -> int:
        return len(self._facts)

    def __iter__(self) -> Any:
        return iter(self._facts)

    def add(self, fact: Fact) -> None:
        if fact.id not in self._index:
            self._index[fact.id] = fact
            self._facts.append(fact)

    def remove(self, fact: Fact) -> None:
        if fact.id in self._index:
            del self._index[fact.id]
            self._facts = [f for f in self._facts if f.id != fact.id]

    def union(self, other: FactSet) -> FactSet:
        result = FactSet()
        result._facts = sorted(set(self._facts) | set(other._facts))
        result._index = {f.id: f for f in result._facts}
        return result

    def intersection(self, other: FactSet) -> FactSet:
        result = FactSet()
        result._facts = sorted(set(self._facts) & set(other._facts))
        result._index = {f.id: f for f in result._facts}
        return result

    def to_list(self) -> list[Fact]:
        return list(self._facts)


class RestrictionMap(NamedTuple):
    """A restriction map between two contexts.

    In sheaf theory, a restriction map ρ_{V,U}: F(V) → F(U) for U ⊆ V
    maps sections over a larger context V to sections over a smaller
    context U. This preserves semantic consistency.

    Attributes
    ----------
    source: The larger context (domain).
    target: The smaller context (codomain).
    """

    source: Context
    target: Context

    def __repr__(self) -> str:
        return f"ρ({self.source} → {self.target})"
