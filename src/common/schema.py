"""Canonical Semantic Fact definition.

This module defines ``SemanticFact``, the single immutable representation
of one semantic fact that every storage engine must map to and from.

Rationale
---------
A semantic fact should represent a *complete event* rather than being
decomposed into triples.  For example a SIGNED event contains:

    actor, contract, organisation, date, regulation, document, confidence, source

all as a single unit.  Decomposing this into binary triples via reification
loses structure and increases join complexity.

The ``SemanticFact`` dataclass preserves the full n-ary structure while
remaining storage-engine-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from common.types import (
    Context,
    Identifier,
    Provenance,
    TemporalInfo,
    Value,
)


@dataclass(slots=True, frozen=True)
class SemanticFact:
    """A single immutable semantic fact — the canonical unit of knowledge.

    Unlike RDF triples, a SemanticFact is an **n-ary structured proposition**
    that preserves the intrinsic structure of events and relationships.

    Parameters
    ----------
    id:
        Globally unique identifier for this fact.
    subject:
        The primary entity the fact is about.
    relation:
        The type of relationship or event.
    objects:
        The values (literals or entity references) participating in the fact.
    attributes:
        Named attributes that qualify the fact (e.g. date, location, quantity).
    context:
        The semantic scope where this fact holds.
    provenance:
        Source, method, and confidence metadata.
    confidence:
        Overall confidence score in [0, 1].  Combined with
        ``provenance.confidence`` this gives a two-level confidence model.
    temporal:
        Optional temporal validity interval.
    metadata:
        Arbitrary additional key-value metadata preserved through round-trips.

    Invariants
    ----------
    1.  Immutable — all fields are frozen.
    2.  Global identifiers — ``id`` is universally unique.
    3.  Roles are unique within ``objects`` (positions are semantically
        meaningful, not duplicated).
    4.  Provenance is preserved — never stripped during serialisation.
    5.  Temporal info is optional — ``None`` means "always valid".
    6.  No semantic information may disappear during serialisation —
        round-tripping is lossless.
    """

    id: Identifier
    subject: Identifier
    relation: Identifier
    objects: tuple[Value, ...] = field(default_factory=tuple)
    attributes: dict[str, Value] = field(default_factory=dict)
    context: Context = field(default_factory=lambda: Context())
    provenance: Provenance = field(default_factory=lambda: Provenance())
    confidence: float = 1.0
    temporal: TemporalInfo | None = None
    metadata: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.subject,
                self.relation,
                self.objects,
                tuple(sorted(self.attributes.items())),
                self.context,
                self.provenance,
                self.confidence,
                self.temporal,
            )
        )

    def arity(self) -> int:
        """Number of object slots (n-ary degree)."""
        return len(self.objects)
