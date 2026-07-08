"""Canonical semantic model and bidirectional mappings.

Mathematical background
-----------------------
The canonical form C is the common semantic space that both the
Knowledge Graph (KG) and Sheaf Database (S) map into.

We define:

    C = { (e₁, r, e₂, ..., eₙ, c) | eᵢ ∈ Entities, r ∈ Relations, c ∈ Contexts }

This is the set of all n-ary grounded facts.

KG triples T ⊂ E × R × E map to C via:
    ι_KG: (s, p, o) ↦ (s, p, o, world)

Sheaf sections S ⊂ ⋃_{U} F(U) map to C via:
    ι_S: (φ, U) ↦ canonicalize(φ) restricted to ⋂{supports}

The key property: ι_KG and ι_S are both injective and their images
overlap exactly on the set of all well-formed semantic facts.

A fact is *well-formed* iff:
    1. All referenced entities exist.
    2. Relation arity matches its signature.
    3. Context is valid.

Complexity
----------
Mapping KG→Canonical: O(1) per triple.
Mapping Sheaf→Canonical: O(k) where k = arity of the section.
Equality check: O(k) where k is the number of component slots.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sfdb.common.types import (
    Context,
    Fact,
    Identifier,
    SemanticType,
    Value,
)


@dataclass(slots=True, frozen=True)
class CanonicalEntity:
    """An entity in the canonical model.

    Every entity has a unique identifier, a type, and a set of
    intrinsic attributes that are independent of any particular relation.
    """

    id: Identifier
    type: SemanticType = SemanticType.ENTITY
    name: str = ""
    attributes: dict[str, Value] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("CanonicalEntity requires a non-empty id")


@dataclass(slots=True, frozen=True)
class CanonicalRelation:
    """A relation signature in the canonical model.

    Defines the expected arity and slot types for a relation.
    This is the schema-level description.
    """

    id: Identifier
    name: str = ""
    arity: int = 1
    slot_types: tuple[SemanticType, ...] = field(default_factory=tuple)
    attributes: dict[str, Value] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class CanonicalFact:
    """A fact in the canonical representation.

    This is the common form that both KG triples and Sheaf sections
    normalize to. Every CanonicalFact is a grounded n-ary proposition.

    A CanonicalFact is *valid* iff:
        len(objects) == relation.arity (if relation is provided and has arity > 0)
        context is non-null
    """

    subject: CanonicalEntity
    relation: CanonicalRelation
    objects: tuple[Value, ...] = field(default_factory=tuple)
    context: Context = field(default_factory=lambda: Context())

    def arity(self) -> int:
        return len(self.objects)

    def to_fact(self) -> Fact:
        """Convert to a generic Fact for storage."""
        return Fact(
            id=Identifier(),
            subject=self.subject.id,
            relation=self.relation.id,
            objects=self.objects,
            context=self.context,
        )


class CanonicalMapping:
    """Bidirectional mapping between a representation and the canonical form.

    This class provides:
        - to_canonical: Convert from KG/Sheaf representation → CanonicalFact
        - from_canonical: Convert from CanonicalFact → KG/Sheaf representation

    The mapping must be invertible up to isomorphism:
        from_canonical(to_canonical(x)) ≅ x
        to_canonical(from_canonical(c)) = c
    """

    def to_canonical(
        self,
        fact: Fact,
        entities: dict[Identifier, CanonicalEntity],
        relations: dict[Identifier, CanonicalRelation],
    ) -> CanonicalFact:
        """Convert a generic Fact to canonical form."""
        subject = entities.get(fact.subject)
        if subject is None:
            subject = CanonicalEntity(id=fact.subject)
        relation = relations.get(fact.relation)
        if relation is None:
            relation = CanonicalRelation(id=fact.relation, arity=fact.arity())
        return CanonicalFact(
            subject=subject,
            relation=relation,
            objects=fact.objects,
            context=fact.context,
        )

    def from_canonical(self, cf: CanonicalFact) -> Fact:
        """Convert a CanonicalFact to a generic Fact."""
        return cf.to_fact()


class CanonicalModel:
    """The full canonical model: entities, relations, and facts.

    This is the *ground truth* representation. Both the KG and Sheaf
    systems must produce the same CanonicalModel for the same input data.
    """

    def __init__(self) -> None:
        self.entities: dict[Identifier, CanonicalEntity] = {}
        self.relations: dict[Identifier, CanonicalRelation] = {}
        self.facts: list[CanonicalFact] = []

    def add_entity(self, entity: CanonicalEntity) -> None:
        self.entities[entity.id] = entity

    def add_relation(self, relation: CanonicalRelation) -> None:
        self.relations[relation.id] = relation

    def add_fact(self, fact: CanonicalFact) -> None:
        self.facts.append(fact)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CanonicalModel):
            return NotImplemented
        return (
            self.entities == other.entities
            and self.relations == other.relations
            and self.facts == other.facts
        )

    def __repr__(self) -> str:
        return (
            f"CanonicalModel("
            f"entities={len(self.entities)}, "
            f"relations={len(self.relations)}, "
            f"facts={len(self.facts)})"
        )
