"""Supporting types for the canonical SemanticFact model.

This module defines the atomic building blocks used by SemanticFact:
identifiers, values, contexts, provenance records, temporal intervals,
and the semantic type enumeration.

Every type here is immutable and hashable where appropriate.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from functools import total_ordering
from typing import Any, NamedTuple


class SemanticType(Enum):
    """The semantic category of a value or entity.

    These types categorise what kind of information a value holds,
    enabling semantic validation and typed restriction maps.
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
    """A globally unique identifier for any semantic object.

    Internally stored as a UUID4 string.  Ordering is by the string
    representation (lexicographic).  Equality and hashing are based on
    the string value alone, making Identifiers safe to use as dict keys
    and set members.

    Complexity: O(1) construction, O(1) comparison.
    """

    _value: str
    __slots__ = ("_value",)

    def __init__(self, value: str | None = None) -> None:
        object.__setattr__(self, "_value", value if value is not None else str(uuid.uuid4()))

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
    """A typed value slot in a SemanticFact.

    A Value can be either a *literal* (string, number, bool) or a *reference*
    to another entity (identified by an Identifier).  The SemanticType
    provides a hint about the role this value plays.

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
        st: SemanticType = object.__getattribute__(self, "_type")
        return st

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
    sub-context of c₂ (c₁ is more specific / narrower).  Facts are
    always stated within a context.

    Examples:
        Context("world")              global knowledge
        Context("world.2024")         temporally scoped
        Context("world.2024.science") domain scoped

    Complexity: O(min(n, m)) comparison where n, m are path depths.
    """

    __slots__ = ("_segments",)

    def __init__(self, path: str = "world", separator: str = ".") -> None:
        object.__setattr__(self, "_segments", tuple(path.split(separator)))

    @property
    def segments(self) -> tuple[str, ...]:
        segs: tuple[str, ...] = object.__getattribute__(self, "_segments")
        return segs

    @property
    def depth(self) -> int:
        return len(self.segments)

    def is_subcontext(self, other: Context) -> bool:
        """True if this context is a sub-context of *other* (more specific).

        c₁ ≤ c₂ iff the path of c₂ is a prefix of c₁'s path.
        """
        segs_self = self.segments
        segs_other = other.segments
        if len(segs_self) < len(segs_other):
            return False
        return segs_self[: len(segs_other)] == segs_other

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
        return self.segments == other.segments

    def __hash__(self) -> int:
        return hash(self.segments)

    def __repr__(self) -> str:
        return f"Ctx({'.'.join(self.segments)})"

    def __str__(self) -> str:
        return ".".join(self.segments)

    def meet(self, other: Context) -> Context:
        """Greatest lower bound (meet) of two contexts."""
        s = self.segments
        o = other.segments
        common: list[str] = []
        for a, b in zip(s, o, strict=False):
            if a == b:
                common.append(a)
            else:
                break
        return Context(".".join(common))

    def join(self, other: Context) -> Context:
        """Least upper bound (join) of two contexts.

        If one is a subcontext of the other, returns the broader.
        Otherwise returns the root.
        """
        if self <= other:
            return other
        if other <= self:
            return self
        return Context("world")


@dataclass(frozen=True)
class Provenance:
    """Provenance metadata for a SemanticFact.

    Records where, when, and by whom a fact was asserted.

    Attributes:
        source:   Human-readable origin (e.g., "web-scraper", "Albert
                  Einstein", "dataset-v2").
        recorded_at:  Timestamp of ingestion (UTC, auto-filled).
        confidence:  Confidence in the source [0, 1].
        method:      How the fact was obtained (e.g., "extraction",
                     "inference", "manual").
    """

    source: str = "unknown"
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: float = 1.0
    method: str = "unknown"


@dataclass(frozen=True)
class TemporalInfo:
    """Temporal validity interval for a SemanticFact.

    The fact holds during [start, end).  If end is None the fact holds
    indefinitely from start onward.
    """

    start: datetime | None = None
    end: datetime | None = None


class RestrictionMap(NamedTuple):
    """A restriction map between two contexts.

    In sheaf theory ρ_{V,U}: F(V) → F(U) for U ⊆ V maps sections
    over a larger context V to sections over a smaller context U.
    """

    source: Context
    target: Context

    def __repr__(self) -> str:
        return f"ρ({self.source} → {self.target})"
