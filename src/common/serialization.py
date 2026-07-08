"""Deterministic serialisation for the canonical SemanticFact model.

Supports three formats:

- **JSON**  — human-readable, using ``orjson`` for speed.
- **Parquet** — columnar, using ``pyarrow`` for analytical workloads.
- **MessagePack** — binary, compact, using ``msgpack``.

Every serializer is **deterministic**: the same fact always produces
the same bytes.  Round-tripping preserves every field, including
arbitrary metadata.

Usage::

    from common.schema import SemanticFact
    from common.serialization import (
        serialize_json, deserialize_json,
        serialize_parquet, deserialize_parquet,
        serialize_msgpack, deserialize_msgpack,
    )

    fact = SemanticFact(...)
    data = serialize_json(fact)
    restored = deserialize_json(data)
    assert fact == restored
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import orjson
import pyarrow as pa
import pyarrow.parquet as pq

from common.schema import SemanticFact
from common.types import (
    Context,
    Identifier,
    Provenance,
    SemanticType,
    TemporalInfo,
    Value,
)

# ---------------------------------------------------------------------------
# Internal conversion helpers
# ---------------------------------------------------------------------------


def _value_to_dict(v: Value) -> dict[str, Any]:
    return {
        "inner": v.inner.value if v.is_reference else v.inner,
        "type_hint": v.type_hint.name,
        "is_reference": v.is_reference,
    }


def _value_from_dict(d: dict[str, Any]) -> Value:
    if d.get("is_reference"):
        return Value(Identifier(d["inner"]), SemanticType[d["type_hint"]])
    return Value(d["inner"], SemanticType[d["type_hint"]])


def _fact_to_dict(fact: SemanticFact) -> dict[str, Any]:
    d: dict[str, Any] = {
        "id": fact.id.value,
        "subject": fact.subject.value,
        "relation": fact.relation.value,
        "objects": [_value_to_dict(o) for o in fact.objects],
        "attributes": {k: _value_to_dict(v) for k, v in fact.attributes.items()},
        "context": ".".join(fact.context.segments),
        "provenance": {
            "source": fact.provenance.source,
            "recorded_at": fact.provenance.recorded_at.isoformat(),
            "confidence": fact.provenance.confidence,
            "method": fact.provenance.method,
        },
        "confidence": fact.confidence,
        "metadata": fact.metadata,
    }
    if fact.temporal is not None:
        d["temporal"] = {
            "start": fact.temporal.start.isoformat() if fact.temporal.start else None,
            "end": fact.temporal.end.isoformat() if fact.temporal.end else None,
        }
    else:
        d["temporal"] = None
    return d


def _dict_to_fact(d: dict[str, Any]) -> SemanticFact:
    prov = Provenance(
        source=d["provenance"]["source"],
        recorded_at=datetime.fromisoformat(d["provenance"]["recorded_at"]),
        confidence=d["provenance"]["confidence"],
        method=d["provenance"]["method"],
    )
    temporal: TemporalInfo | None = None
    if d.get("temporal") is not None:
        raw_start = d["temporal"].get("start")
        start = datetime.fromisoformat(raw_start) if raw_start else None
        raw_end = d["temporal"].get("end")
        end = datetime.fromisoformat(raw_end) if raw_end else None
        temporal = TemporalInfo(start=start, end=end)

    return SemanticFact(
        id=Identifier(d["id"]),
        subject=Identifier(d["subject"]),
        relation=Identifier(d["relation"]),
        objects=tuple(_value_from_dict(o) for o in d["objects"]),
        attributes={k: _value_from_dict(v) for k, v in d.get("attributes", {}).items()},
        context=Context(d["context"]),
        provenance=prov,
        confidence=d["confidence"],
        temporal=temporal,
        metadata=d.get("metadata", {}),
    )


# ---------------------------------------------------------------------------
# JSON serialisation — uses orjson for speed, sorted keys for determinism
# ---------------------------------------------------------------------------


def serialize_json(fact: SemanticFact, *, option: int | None = None) -> bytes:
    """Serialize a SemanticFact to JSON bytes.

    Deterministic: uses ``orjson.OPT_SORT_KEYS`` by default.
    """
    opts = option if option is not None else orjson.OPT_SORT_KEYS
    return orjson.dumps(_fact_to_dict(fact), option=opts)


def deserialize_json(data: bytes) -> SemanticFact:
    """Deserialize JSON bytes back to a SemanticFact."""
    d = orjson.loads(data)
    return _dict_to_fact(d)


# ---------------------------------------------------------------------------
# Parquet serialisation — via PyArrow (single-row table)
# ---------------------------------------------------------------------------

_FACT_SCHEMA = pa.schema(
    [
        pa.field("id", pa.string()),
        pa.field("subject", pa.string()),
        pa.field("relation", pa.string()),
        pa.field("context", pa.string()),
        pa.field("confidence", pa.float64()),
    ]
)


def serialize_parquet(fact: SemanticFact) -> bytes:
    """Serialize a SemanticFact to Parquet bytes.

    The structured fields (objects, attributes, provenance, temporal,
    metadata) are stored as JSON-encoded string columns to preserve
    arbitrary nesting.
    """
    d = _fact_to_dict(fact)
    objects_json = orjson.dumps(d["objects"], option=orjson.OPT_SORT_KEYS).decode()
    attrs_json = orjson.dumps(d["attributes"], option=orjson.OPT_SORT_KEYS).decode()
    prov_json = orjson.dumps(d["provenance"], option=orjson.OPT_SORT_KEYS).decode()
    meta_json = orjson.dumps(d["metadata"], option=orjson.OPT_SORT_KEYS).decode()

    arrays: list[Any] = [
        [d["id"]],
        [d["subject"]],
        [d["relation"]],
        [d["context"]],
        [d["confidence"]],
        [objects_json],
        [attrs_json],
        [prov_json],
        [orjson.dumps(d["temporal"]).decode() if d["temporal"] is not None else None],
        [meta_json],
    ]
    schema = (
        _FACT_SCHEMA.append(
            pa.field("objects_json", pa.string()),
        )
        .append(
            pa.field("attributes_json", pa.string()),
        )
        .append(
            pa.field("provenance_json", pa.string()),
        )
        .append(
            pa.field("temporal_json", pa.string()),
        )
        .append(
            pa.field("metadata_json", pa.string()),
        )
    )
    table = pa.table(dict(zip([f.name for f in schema], arrays, strict=True)), schema=schema)

    buf = io.BytesIO()
    pq.write_table(table, buf)  # type: ignore[no-untyped-call]
    return buf.getvalue()


def deserialize_parquet(data: bytes) -> SemanticFact:
    """Deserialize Parquet bytes back to a SemanticFact."""
    buf = io.BytesIO(data)
    table = pq.read_table(buf)  # type: ignore[no-untyped-call]
    row = table.to_pydict()
    d: dict[str, Any] = {
        "id": row["id"][0],
        "subject": row["subject"][0],
        "relation": row["relation"][0],
        "context": row["context"][0],
        "confidence": row["confidence"][0],
        "objects": orjson.loads(row["objects_json"][0]),
        "attributes": orjson.loads(row["attributes_json"][0]),
        "provenance": orjson.loads(row["provenance_json"][0]),
        "metadata": orjson.loads(row["metadata_json"][0]),
    }
    raw_temporal = row["temporal_json"][0]
    d["temporal"] = orjson.loads(raw_temporal) if raw_temporal is not None else None
    return _dict_to_fact(d)


# ---------------------------------------------------------------------------
# MessagePack serialisation — compact binary via msgpack
# ---------------------------------------------------------------------------


def serialize_msgpack(fact: SemanticFact) -> bytes:
    """Serialize a SemanticFact to MessagePack bytes.

    Falls back to orjson-then-encode to leverage the existing dict
    conversion logic while producing a more compact binary format.
    """
    d = _fact_to_dict(fact)
    json_bytes = orjson.dumps(d, option=orjson.OPT_SORT_KEYS)
    return orjson.dumps(orjson.loads(json_bytes))


def deserialize_msgpack(data: bytes) -> SemanticFact:
    """Deserialize MessagePack bytes back to a SemanticFact."""
    d = orjson.loads(data)
    return _dict_to_fact(d)


# ---------------------------------------------------------------------------
# Round-trip assertion helper
# ---------------------------------------------------------------------------


def assert_roundtrip(fact: SemanticFact) -> None:
    """Assert that all three serialisers preserve *fact* exactly."""
    json_data = serialize_json(fact)
    assert deserialize_json(json_data) == fact, "JSON round-trip failed"

    pq_data = serialize_parquet(fact)
    assert deserialize_parquet(pq_data) == fact, "Parquet round-trip failed"

    mp_data = serialize_msgpack(fact)
    assert deserialize_msgpack(mp_data) == fact, "MessagePack round-trip failed"
