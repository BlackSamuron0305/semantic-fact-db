"""Tests for SemanticFact serialisation — JSON, Parquet, MessagePack."""

from datetime import UTC

import hypothesis.strategies as st
from hypothesis import given

from common.schema import SemanticFact
from common.serialization import (
    assert_roundtrip,
    deserialize_json,
    deserialize_msgpack,
    deserialize_parquet,
    serialize_json,
    serialize_msgpack,
    serialize_parquet,
)
from common.types import Context, Identifier, Provenance, TemporalInfo, Value

# ---------------------------------------------------------------------------
# Hypothesis strategies for generating random SemanticFacts
# ---------------------------------------------------------------------------

st_identifiers = st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_-")
st_literals = st.one_of(
    st.text(max_size=50),
    st.integers(min_value=-(10**9), max_value=10**9),
    st.floats(allow_nan=False, allow_infinity=False),
)
st_values = st.one_of(
    st.builds(Value.literal, st_literals),
    st.builds(Value.reference, st.builds(Identifier, st_identifiers)),
)


@given(st.lists(st_values, max_size=5))
def test_json_roundtrip(values: list[Value]) -> None:
    fact = SemanticFact(
        id=Identifier("test-id"),
        subject=Identifier("test-subject"),
        relation=Identifier("test-relation"),
        objects=tuple(values),
    )
    data = serialize_json(fact)
    restored = deserialize_json(data)
    assert fact == restored, f"JSON round-trip failed for {fact}"


@given(st.lists(st_values, max_size=5))
def test_parquet_roundtrip(values: list[Value]) -> None:
    fact = SemanticFact(
        id=Identifier("test-id"),
        subject=Identifier("test-subject"),
        relation=Identifier("test-relation"),
        objects=tuple(values),
    )
    data = serialize_parquet(fact)
    restored = deserialize_parquet(data)
    assert fact == restored, f"Parquet round-trip failed for {fact}"


@given(st.lists(st_values, max_size=5))
def test_msgpack_roundtrip(values: list[Value]) -> None:
    fact = SemanticFact(
        id=Identifier("test-id"),
        subject=Identifier("test-subject"),
        relation=Identifier("test-relation"),
        objects=tuple(values),
    )
    data = serialize_msgpack(fact)
    restored = deserialize_msgpack(data)
    assert fact == restored, f"Msgpack round-trip failed for {fact}"


@given(st.lists(st_values, max_size=5))
def test_roundtrip_with_temporal(values: list[Value]) -> None:
    from datetime import datetime

    fact = SemanticFact(
        id=Identifier("test-id"),
        subject=Identifier("test-subject"),
        relation=Identifier("test-relation"),
        objects=tuple(values),
        temporal=TemporalInfo(
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 12, 31, tzinfo=UTC),
        ),
    )
    assert_roundtrip(fact)


@given(st.lists(st_values, max_size=5))
def test_roundtrip_with_provenance(values: list[Value]) -> None:
    fact = SemanticFact(
        id=Identifier("test-id"),
        subject=Identifier("test-subject"),
        relation=Identifier("test-relation"),
        objects=tuple(values),
        provenance=Provenance(source="hypothesis-test", method="property-based", confidence=0.8),
    )
    assert_roundtrip(fact)


@given(st.lists(st_values, max_size=5))
def test_roundtrip_with_metadata(values: list[Value]) -> None:
    fact = SemanticFact(
        id=Identifier("test-id"),
        subject=Identifier("test-subject"),
        relation=Identifier("test-relation"),
        objects=tuple(values),
        metadata={"hypothesis_run": True, "iteration": 42},
    )
    assert_roundtrip(fact)


@given(st.lists(st_values, max_size=5))
def test_roundtrip_all_features(values: list[Value]) -> None:
    from datetime import datetime

    fact = SemanticFact(
        id=Identifier("test-id"),
        subject=Identifier("test-subject"),
        relation=Identifier("test-relation"),
        objects=tuple(values),
        attributes={"key1": Value.literal("val1")},
        context=Context("world.test"),
        provenance=Provenance(source="test", method="auto", confidence=0.9),
        confidence=0.75,
        temporal=TemporalInfo(
            start=datetime(2023, 6, 1, tzinfo=UTC),
        ),
        metadata={"version": 2},
    )
    assert_roundtrip(fact)
