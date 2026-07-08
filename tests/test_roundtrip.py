"""Round-trip tests: insert facts, serialize, deserialize, verify identity."""

from common.schema import SemanticFact
from common.serialization import (
    deserialize_json,
    deserialize_msgpack,
    deserialize_parquet,
    serialize_json,
    serialize_msgpack,
    serialize_parquet,
)
from common.types import Context, Identifier, Provenance, TemporalInfo, Value


def _make_sample_facts() -> list[SemanticFact]:
    return [
        SemanticFact(
            id=Identifier("fact-001"),
            subject=Identifier("alice"),
            relation=Identifier("knows"),
            objects=(Value.reference(Identifier("bob")),),
        ),
        SemanticFact(
            id=Identifier("fact-002"),
            subject=Identifier("alice"),
            relation=Identifier("signed"),
            objects=(
                Value.reference(Identifier("contract-42")),
                Value.literal("2024-03-15"),
                Value.reference(Identifier("acme-corp")),
            ),
            attributes={
                "regulation": Value.literal("GDPR"),
                "jurisdiction": Value.literal("EU"),
            },
            context=Context("world.2024.contracts"),
            provenance=Provenance(
                source="manual-entry",
                method="human-annotation",
                confidence=0.95,
            ),
            confidence=0.98,
            temporal=TemporalInfo(
                start=__import__("datetime").datetime(2024, 3, 15),
            ),
            metadata={"entered_by": "laith"},
        ),
        SemanticFact(
            id=Identifier("fact-003"),
            subject=Identifier("bob"),
            relation=Identifier("age"),
            objects=(Value.literal(42),),
            context=Context("world.people"),
        ),
    ]


class TestJSONRoundTrip:
    def test_roundtrip_preserves_all_fields(self) -> None:
        for original in _make_sample_facts():
            data = serialize_json(original)
            restored = deserialize_json(data)
            assert restored == original
            assert restored.id == original.id
            assert restored.subject == original.subject
            assert restored.relation == original.relation
            assert restored.objects == original.objects
            assert restored.attributes == original.attributes
            assert restored.context == original.context
            assert restored.provenance == original.provenance
            assert restored.confidence == original.confidence
            assert restored.metadata == original.metadata

    def test_deterministic_json(self) -> None:
        fact = _make_sample_facts()[0]
        data1 = serialize_json(fact)
        data2 = serialize_json(fact)
        assert data1 == data2


class TestParquetRoundTrip:
    def test_roundtrip_preserves_all_fields(self) -> None:
        for original in _make_sample_facts():
            data = serialize_parquet(original)
            restored = deserialize_parquet(data)
            assert restored == original

    def test_deterministic_parquet(self) -> None:
        fact = _make_sample_facts()[0]
        data1 = serialize_parquet(fact)
        data2 = serialize_parquet(fact)
        assert data1 == data2


class TestMsgPackRoundTrip:
    def test_roundtrip_preserves_all_fields(self) -> None:
        for original in _make_sample_facts():
            data = serialize_msgpack(original)
            restored = deserialize_msgpack(data)
            assert restored == original

    def test_deterministic_msgpack(self) -> None:
        fact = _make_sample_facts()[0]
        data1 = serialize_msgpack(fact)
        data2 = serialize_msgpack(fact)
        assert data1 == data2
