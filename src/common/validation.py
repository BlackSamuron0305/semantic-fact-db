"""Invariant checking for the canonical SemanticFact model.

Every function in this module returns a list of violation messages.
An empty list means the fact (or collection) is valid.
"""

from __future__ import annotations

from common.schema import SemanticFact
from common.types import Identifier, SemanticType, Value


def check_fact_invariants(fact: SemanticFact) -> list[str]:
    """Check all invariants for a single SemanticFact.

    Returns a list of human-readable violation messages (empty = valid).
    """
    errors: list[str] = []

    # 1. Identifier is present and non-empty
    if not fact.id.value:
        errors.append("Fact id is empty")

    # 2. Subject is present and non-empty
    if not fact.subject.value:
        errors.append("Fact subject is empty")

    # 3. Relation is present and non-empty
    if not fact.relation.value:
        errors.append("Fact relation is empty")

    # 4. Confidence in [0, 1]
    if not 0.0 <= fact.confidence <= 1.0:
        errors.append(f"Confidence {fact.confidence} outside [0, 1]")

    # 5. Provenance confidence in [0, 1]
    if not 0.0 <= fact.provenance.confidence <= 1.0:
        errors.append(f"Provenance confidence {fact.provenance.confidence} outside [0, 1]")

    # 6. Temporal: if end is specified, start must also be specified
    if fact.temporal is not None and fact.temporal.end is not None and fact.temporal.start is None:
        errors.append("Temporal end specified without start")

    # 7. Temporal: end must not precede start
    if (
        fact.temporal is not None
        and fact.temporal.start is not None
        and fact.temporal.end is not None
        and fact.temporal.end < fact.temporal.start
    ):
        errors.append("Temporal end precedes start")

    return errors


def check_fact_collection(facts: list[SemanticFact]) -> list[str]:
    """Check invariants across a collection of facts.

    Verifies referential integrity, duplicate IDs, and global validity.
    """
    errors: list[str] = []
    seen_ids: set[str] = set()
    all_ids: set[str] = {f.id.value for f in facts}

    for fact in facts:
        errors.extend(check_fact_invariants(fact))

        # Duplicate ID check
        if fact.id.value in seen_ids:
            errors.append(f"Duplicate fact id: {fact.id}")
        seen_ids.add(fact.id.value)

        # Referential integrity — every referenced entity should exist
        _check_references(fact, all_ids, errors)

    return errors


def _check_references(fact: SemanticFact, known_ids: set[str], errors: list[str]) -> None:
    """Check that every referenced entity is in *known_ids*."""
    refs = {fact.subject.value}
    for obj in fact.objects:
        if obj.is_reference:
            inner = obj.inner
            if isinstance(inner, Identifier):
                refs.add(inner.value)
    for rid in refs:
        if rid not in known_ids:
            errors.append(f"Referenced entity {rid} not found in collection (fact {fact.id})")


def is_valid_type_for_role(value: Value, expected: SemanticType | None) -> bool:
    """Check that a Value's type matches the expected role type.

    Returns True if *expected* is None (no constraint) or types match.
    """
    if expected is None:
        return True
    return value.type_hint == expected
