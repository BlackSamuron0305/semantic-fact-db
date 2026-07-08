"""Identifier generation and validation utilities.

Strategies
----------
- *UUID4*: default, globally unique.
- *Prefixed*: human-readable with a domain prefix (e.g. ``person/...``).
- *Derived*: deterministic hash of the fact content for content-addressing.
"""

from __future__ import annotations

import hashlib
import uuid

from common.types import Identifier


def new_id() -> Identifier:
    """Generate a new random UUID4-based Identifier."""
    return Identifier()


def prefixed_id(prefix: str, local_id: str | None = None) -> Identifier:
    """Generate an Identifier with a human-readable prefix.

    Example::

        prefixed_id("person")            -> person/<uuid>
        prefixed_id("person", "alice")   -> person/alice
    """
    inner = f"{prefix}/{local_id}" if local_id else f"{prefix}/{uuid.uuid4()}"
    return Identifier(inner)


def content_hash_id(fact_bytes: bytes) -> Identifier:
    """Deterministic content-addressed Identifier.

    Uses SHA-256 of the serialised fact bytes.  Two identical facts
    will always produce the same Identifier.
    """
    digest = hashlib.sha256(fact_bytes).hexdigest()
    return Identifier(digest)


def is_valid_uuid(value: str) -> bool:
    """Return True if *value* is a valid UUID4 string."""
    try:
        uuid.UUID(value, version=4)
        return True
    except (ValueError, AttributeError):
        return False
