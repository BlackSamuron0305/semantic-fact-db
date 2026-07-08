"""Canonical representation bridging KG and Sheaf subsystems.

This module defines the canonical intermediate representation that
ensures semantic equivalence between KG triples and sheaf sections.
Every KG triple and every sheaf fact maps to a unique canonical form,
and the mapping is invertible.

This is the *proof layer*: the canonical form is the common semantic
denominator that both systems must agree on.
"""

from sfdb.canonical.canonical import (
    CanonicalEntity,
    CanonicalFact,
    CanonicalMapping,
    CanonicalModel,
    CanonicalRelation,
)

__all__ = [
    "CanonicalEntity",
    "CanonicalFact",
    "CanonicalMapping",
    "CanonicalModel",
    "CanonicalRelation",
]
