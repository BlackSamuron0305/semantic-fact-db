"""Equivalence tests for the KG-mem control variant.

The in-memory KG engine (``storage="memory"``) must be observationally
identical to the SQLite-backed KG engine on every query class the paper
benchmarks — it exists purely to isolate the storage layer as a
variable, so any semantic divergence between the two would invalidate
the control.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from common.interfaces import Query, QueryType
from common.types import Identifier
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts
from sfdb.kg.engine import KnowledgeGraphEngine, MemoryDictionaryEncoder, MemoryIndexManager

N_FACTS = 300


@pytest.fixture(scope="module")
def facts() -> list[Any]:
    config = SyntheticConfig(num_facts=N_FACTS, num_entities=max(20, N_FACTS // 10), seed=42)
    return list(generate_facts(config).facts)


@pytest.fixture
def sqlite_engine(facts: list[Any]) -> Iterator[KnowledgeGraphEngine]:
    eng = KnowledgeGraphEngine(name="test_kg_sqlite")
    eng.create()
    for f in facts:
        eng.insert(f)
    yield eng
    eng.drop()


@pytest.fixture
def memory_engine(facts: list[Any]) -> Iterator[KnowledgeGraphEngine]:
    eng = KnowledgeGraphEngine(name="test_kg_memory")
    eng.create({"storage": "memory"})
    for f in facts:
        eng.insert(f)
    yield eng
    eng.drop()


def _canonical(result_facts: Any) -> set[tuple[Any, ...]]:
    rows = set()
    for f in result_facts:
        rows.add(
            (
                str(f.id),
                str(f.subject),
                str(f.relation),
                tuple(str(o.inner) for o in f.objects),
                str(f.context),
            )
        )
    return rows


QUERIES = [
    ("LOOKUP", Query(query_type=QueryType.LOOKUP, subject=Identifier("entity_0"), limit=10_000)),
    ("GLOBAL", Query(query_type=QueryType.GLOBAL, limit=10_000)),
    (
        "TEMPORAL_BOUNDED",
        Query(
            query_type=QueryType.TEMPORAL,
            temporal_start="2022",
            temporal_end="2023",
            limit=10_000,
        ),
    ),
    (
        "TEMPORAL_UNBOUNDED",
        Query(
            query_type=QueryType.TEMPORAL,
            temporal_start="2023-01-01T00:00:00+00:00",
            temporal_end=None,
            limit=10_000,
        ),
    ),
    (
        "NEIGHBORHOOD",
        Query(query_type=QueryType.NEIGHBORHOOD, subject=Identifier("entity_0"), limit=10_000),
    ),
    ("CONTEXT", Query(query_type=QueryType.CONTEXT, context="world", limit=10_000)),
]


class TestMemoryVariantEquivalence:
    def test_uses_memory_storage_layer(self, memory_engine: KnowledgeGraphEngine) -> None:
        assert isinstance(memory_engine._encoder, MemoryDictionaryEncoder)
        assert isinstance(memory_engine._indexes, MemoryIndexManager)

    @pytest.mark.parametrize(("label", "query"), QUERIES, ids=[q[0] for q in QUERIES])
    def test_query_class_equivalence(
        self,
        sqlite_engine: KnowledgeGraphEngine,
        memory_engine: KnowledgeGraphEngine,
        label: str,
        query: Query,
    ) -> None:
        sqlite_rows = _canonical(sqlite_engine.query(query).facts)
        memory_rows = _canonical(memory_engine.query(query).facts)
        assert sqlite_rows == memory_rows, (
            f"{label}: KG-mem diverges from KG "
            f"({len(sqlite_rows - memory_rows)} rows only in sqlite, "
            f"{len(memory_rows - sqlite_rows)} only in memory)"
        )
        assert len(sqlite_rows) > 0, f"{label}: empty result set makes this test vacuous"

    def test_delete_equivalence(
        self,
        sqlite_engine: KnowledgeGraphEngine,
        memory_engine: KnowledgeGraphEngine,
        facts: list[Any],
    ) -> None:
        victim = facts[0]
        for eng in (sqlite_engine, memory_engine):
            result = eng.delete(victim.id)
            assert result.success
        q = Query(query_type=QueryType.GLOBAL, limit=10_000)
        sqlite_rows = _canonical(sqlite_engine.query(q).facts)
        memory_rows = _canonical(memory_engine.query(q).facts)
        assert sqlite_rows == memory_rows
        assert all(row[0] != victim.id.value for row in memory_rows)

    def test_delete_missing_fact_fails_identically(
        self,
        sqlite_engine: KnowledgeGraphEngine,
        memory_engine: KnowledgeGraphEngine,
    ) -> None:
        ghost = Identifier("no_such_fact_id")
        assert not sqlite_engine.delete(ghost).success
        assert not memory_engine.delete(ghost).success

    def test_triple_counts_match(
        self,
        sqlite_engine: KnowledgeGraphEngine,
        memory_engine: KnowledgeGraphEngine,
    ) -> None:
        assert sqlite_engine._indexes is not None
        assert memory_engine._indexes is not None
        assert sqlite_engine._indexes.count() == memory_engine._indexes.count()

    def test_verify_passes(self, memory_engine: KnowledgeGraphEngine) -> None:
        assert memory_engine.verify().valid
