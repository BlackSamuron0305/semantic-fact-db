"""Serialization and storage statistics.

Provides serialization to Arrow IPC format and JSON for all core types.
Also computes storage statistics (byte sizes, compression ratios) for
benchmark comparison.

Complexity
----------
Serialize: O(n) where n = number of items.
Deserialize: O(n).
Storage stats: O(n) for size computation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import orjson

from sfdb.canonical.canonical import CanonicalEntity, CanonicalModel
from sfdb.common.types import Context, Fact, Identifier, Value
from sfdb.kg.triple import Triple
from sfdb.sheaf.sheaf import Section


@dataclass(slots=True, frozen=True)
class StorageStats:
    """Storage statistics for a representation.

    Attributes
    ----------
    num_items: Number of items stored.
    bytes_raw: Estimated raw byte size.
    bytes_serialized: Size after serialization.
    bytes_per_item: Average bytes per item.
    """

    num_items: int
    bytes_raw: int
    bytes_serialized: int
    bytes_per_item: float = 0.0

    def __post_init__(self) -> None:
        if self.num_items > 0 and self.bytes_per_item == 0.0:
            object.__setattr__(
                self,
                "bytes_per_item",
                self.bytes_serialized / self.num_items,
            )


class FactSerializer:
    """Serialize/deserialize Facts to/from JSON-compatible dicts.

    Uses orjson for fast serialization.
    """

    @staticmethod
    def to_dict(fact: Fact) -> dict[str, Any]:
        return {
            "id": fact.id.value,
            "subject": fact.subject.value,
            "relation": fact.relation.value,
            "objects": [
                {
                    "type": "ref" if v.is_reference else "lit",
                    "value": v.inner.value if v.is_reference else v.inner,
                    "semantic_type": v.type_hint.name,
                }
                for v in fact.objects
            ],
            "context": str(fact.context),
            "confidence": fact.confidence,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Fact:
        objects = []
        for od in d["objects"]:
            if od["type"] == "ref":
                objects.append(Value.reference(Identifier(od["value"])))
            else:
                objects.append(Value.literal(od["value"]))
        return Fact(
            id=Identifier(d["id"]),
            subject=Identifier(d["subject"]),
            relation=Identifier(d["relation"]),
            objects=tuple(objects),
            context=Context(d["context"]),
            confidence=d.get("confidence", 1.0),
        )

    @staticmethod
    def serialize(facts: list[Fact]) -> bytes:
        return orjson.dumps([FactSerializer.to_dict(f) for f in facts])

    @staticmethod
    def deserialize(data: bytes) -> list[Fact]:
        return [FactSerializer.from_dict(d) for d in orjson.loads(data)]


class TripleSerializer:
    """Serialize/deserialize Triples."""

    @staticmethod
    def to_dict(triple: Triple) -> dict[str, Any]:
        return {
            "subject": triple.subject.value,
            "predicate": triple.predicate.value,
            "obj": triple.obj.value,
            "context": str(triple.context),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Triple:
        return Triple(
            subject=Identifier(d["subject"]),
            predicate=Identifier(d["predicate"]),
            obj=Identifier(d["obj"]),
            context=Context(d["context"]),
        )

    @staticmethod
    def serialize(triples: list[Triple]) -> bytes:
        return orjson.dumps([TripleSerializer.to_dict(t) for t in triples])

    @staticmethod
    def deserialize(data: bytes) -> list[Triple]:
        return [TripleSerializer.from_dict(d) for d in orjson.loads(data)]


class SectionSerializer:
    """Serialize/deserialize Sheaf Sections."""

    @staticmethod
    def to_dict(section: Section) -> dict[str, Any]:
        return {
            "fact": FactSerializer.to_dict(section.fact),
            "context": str(section.context),
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Section:
        return Section(
            fact=FactSerializer.from_dict(d["fact"]),
            context=Context(d["context"]),
        )

    @staticmethod
    def serialize(sections: list[Section]) -> bytes:
        return orjson.dumps([SectionSerializer.to_dict(s) for s in sections])

    @staticmethod
    def deserialize(data: bytes) -> list[Section]:
        return [SectionSerializer.from_dict(d) for d in orjson.loads(data)]


class CanonicalSerializer:
    """Serialize/deserialize CanonicalModels."""

    @staticmethod
    def serialize(model: CanonicalModel) -> bytes:
        facts = [FactSerializer.to_dict(f.to_fact()) for f in model.facts]
        return orjson.dumps(
            {
                "entities": [
                    {"id": e.id.value, "type": e.type.name, "name": e.name}
                    for e in model.entities.values()
                ],
                "facts": facts,
            }
        )

    @staticmethod
    def deserialize(data: bytes) -> CanonicalModel:
        d = orjson.loads(data)
        model = CanonicalModel()
        for ed in d.get("entities", []):
            model.add_entity(
                CanonicalEntity(
                    id=Identifier(ed["id"]),
                )
            )
        # TODO: add relations and facts from serialized form
        return model


def compute_storage_stats(items: list[Any], serializer: Any) -> StorageStats:
    """Compute storage statistics for a list of items."""
    raw = sum(obj.__sizeof__() for obj in items)
    serialized = len(serializer.serialize(items))
    return StorageStats(
        num_items=len(items),
        bytes_raw=raw,
        bytes_serialized=serialized,
    )
