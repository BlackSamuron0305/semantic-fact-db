"""Semantic Fact Database (SFDB).

A sheaf-theoretic approach to semantic knowledge representation.
Investigates whether sheaf-based representations can preserve semantic
equivalence while reducing computational cost vs. traditional knowledge graphs.

Research hypothesis: Semantic facts can be represented directly rather than
decomposed into triples, enabling local queries via restriction maps while
preserving global consistency through sheaf conditions.
"""

__version__ = "0.1.0"

from sfdb.canonical import CanonicalEntity, CanonicalFact, CanonicalRelation
from sfdb.common import Fact, Identifier, SemanticType, Value

__all__ = [
    "CanonicalEntity",
    "CanonicalFact",
    "CanonicalRelation",
    "Fact",
    "Identifier",
    "SemanticType",
    "Value",
]
