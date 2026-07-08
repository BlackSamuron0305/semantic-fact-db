"""Common base types and data structures for SFDB.

This module defines the fundamental atoms of the semantic representation:
facts, identifiers, values, and semantic types. These types are used by
both the KG and Sheaf subsystems.

The design treats a *fact* as the primitive unit — not a triple.
A fact is a structured proposition: (subject, relation, objects, context, metadata).
This avoids premature decomposition into binary predicates.
"""

from sfdb.common.types import (
    Context,
    Fact,
    FactSet,
    Identifier,
    RestrictionMap,
    SemanticType,
    Value,
)

__all__ = [
    "Context",
    "Fact",
    "FactSet",
    "Identifier",
    "RestrictionMap",
    "SemanticType",
    "Value",
]
