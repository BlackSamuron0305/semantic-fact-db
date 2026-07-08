"""KnowledgeGraphEngine — baseline RDF-style triple store.

This module implements the reference Knowledge Graph storage engine
that serves as the benchmark baseline.  It uses dictionary encoding
for entities/predicates/literals, SQLite-backed persistence with
SPO/POS/OPS indexes, and RDF-style reification for n-ary facts.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from common.exceptions import QueryError, StorageError
from common.interfaces import (
    DatabaseEngine,
    DeleteResult,
    EngineStatistics,
    EngineType,
    ExecutionPlan,
    InsertResult,
    Query,
    QueryResult,
    QueryType,
    StorageFormat,
    UpdateResult,
    VerificationResult,
)
from common.schema import SemanticFact
from common.serialization import (
    deserialize_json,
    deserialize_msgpack,
    serialize_json,
    serialize_msgpack,
)
from common.types import Context, Identifier, Provenance, TemporalInfo, Value

# ---------------------------------------------------------------------------
# Built-in predicates for reification
# ---------------------------------------------------------------------------

RDF_TYPE = "rdf:type"
RDF_SUBJECT = "rdf:subject"
RDF_PREDICATE = "rdf:predicate"
RDF_OBJECT = "rdf:object"
SFDB_FACT = "sfdb:Fact"
SFDB_CONTEXT = "sfdb:context"
SFDB_CONFIDENCE = "sfdb:confidence"
SFDB_PROV_SOURCE = "sfdb:provSource"
SFDB_PROV_RECORDED = "sfdb:provRecordedAt"
SFDB_PROV_CONFIDENCE = "sfdb:provConfidence"
SFDB_PROV_METHOD = "sfdb:provMethod"
SFDB_TEMPORAL_START = "sfdb:temporalStart"
SFDB_TEMPORAL_END = "sfdb:temporalEnd"
SFDB_ATTR_PREFIX = "sfdb:attr_"

OBJECT_TYPE_ENTITY = "entity"
OBJECT_TYPE_LITERAL = "literal"

# ---------------------------------------------------------------------------
# Helper types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EncodedTriple:
    subject_id: int
    predicate_id: int
    object_id: int
    object_type: str
    event_id: int
    role: str
    context: str


@dataclass
class BenchmarkHooks:
    insert_times: list[float] = field(default_factory=list)
    lookup_times: list[float] = field(default_factory=list)
    join_times: list[float] = field(default_factory=list)
    path_times: list[float] = field(default_factory=list)
    planning_times: list[float] = field(default_factory=list)
    execution_times: list[float] = field(default_factory=list)
    memory_samples: list[int] = field(default_factory=list)

    def record_insert(self, ns: float) -> None:
        self.insert_times.append(ns)

    def record_lookup(self, ns: float) -> None:
        self.lookup_times.append(ns)

    def record_join(self, ns: float) -> None:
        self.join_times.append(ns)

    def record_path(self, ns: float) -> None:
        self.path_times.append(ns)

    def record_planning(self, ns: float) -> None:
        self.planning_times.append(ns)

    def record_execution(self, ns: float) -> None:
        self.execution_times.append(ns)


# ---------------------------------------------------------------------------
# Dictionary encoding
# ---------------------------------------------------------------------------


class DictionaryEncoder:
    """Manages entity/predicate/literal dictionary tables in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._entity_cache: dict[str, int] = {}
        self._predicate_cache: dict[str, int] = {}
        self._literal_cache: dict[str, int] = {}

    def create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS entity_dict (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS predicate_dict (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS literal_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'string'
            );
            CREATE INDEX IF NOT EXISTS idx_entity_name ON entity_dict(name);
            CREATE INDEX IF NOT EXISTS idx_predicate_name ON predicate_dict(name);
        """)
        self._load_caches()

    def _load_caches(self) -> None:
        for row in self._conn.execute("SELECT id, name FROM entity_dict"):
            self._entity_cache[row[1]] = row[0]
        for row in self._conn.execute("SELECT id, name FROM predicate_dict"):
            self._predicate_cache[row[1]] = row[0]
        for row in self._conn.execute("SELECT id, value, type FROM literal_table"):
            self._literal_cache[f"{row[1]}|{row[2]}"] = row[0]

    def encode_entity(self, name: str) -> int:
        if name in self._entity_cache:
            return self._entity_cache[name]
        cur = self._conn.execute("INSERT OR IGNORE INTO entity_dict(name) VALUES (?)", (name,))
        cur = self._conn.execute("SELECT id FROM entity_dict WHERE name = ?", (name,))
        eid = cur.fetchone()[0]
        self._entity_cache[name] = eid
        return eid

    def encode_predicate(self, name: str) -> int:
        if name in self._predicate_cache:
            return self._predicate_cache[name]
        cur = self._conn.execute("INSERT OR IGNORE INTO predicate_dict(name) VALUES (?)", (name,))
        cur = self._conn.execute("SELECT id FROM predicate_dict WHERE name = ?", (name,))
        pid = cur.fetchone()[0]
        self._predicate_cache[name] = pid
        return pid

    def encode_literal(self, value: str, typ: str = "string") -> int:
        key = f"{value}|{typ}"
        if key in self._literal_cache:
            return self._literal_cache[key]
        cur = self._conn.execute(
            "INSERT INTO literal_table(value, type) VALUES (?, ?)", (value, typ)
        )
        lid = cur.lastrowid
        if lid is None:
            cur = self._conn.execute(
                "SELECT id FROM literal_table WHERE value = ? AND type = ?", (value, typ)
            )
            lid = cur.fetchone()[0]
        self._literal_cache[key] = lid
        return lid

    def decode_entity(self, eid: int) -> str | None:
        for name, eid2 in self._entity_cache.items():
            if eid2 == eid:
                return name
        cur = self._conn.execute("SELECT name FROM entity_dict WHERE id = ?", (eid,))
        row = cur.fetchone()
        if row is not None:
            self._entity_cache[row[0]] = eid
        return row[0] if row else None

    def decode_predicate(self, pid: int) -> str | None:
        for name, pid2 in self._predicate_cache.items():
            if pid2 == pid:
                return name
        cur = self._conn.execute("SELECT name FROM predicate_dict WHERE id = ?", (pid,))
        row = cur.fetchone()
        if row is not None:
            self._predicate_cache[row[0]] = pid
        return row[0] if row else None

    def decode_literal(self, lid: int) -> tuple[str, str] | None:
        for key, lid2 in self._literal_cache.items():
            if lid2 == lid:
                parts = key.split("|", 1)
                return (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "string")
        cur = self._conn.execute("SELECT value, type FROM literal_table WHERE id = ?", (lid,))
        row = cur.fetchone()
        return row if row else None

    def entity_count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM entity_dict")
        return cur.fetchone()[0]

    def predicate_count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM predicate_dict")
        return cur.fetchone()[0]

    def literal_count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM literal_table")
        return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Triple index manager
# ---------------------------------------------------------------------------


class IndexManager:
    """Manages SPO/POS/OPS indexes (optionally 6-index mode)."""

    def __init__(self, conn: sqlite3.Connection, six_index: bool = False) -> None:
        self._conn = conn
        self._six_index = six_index

    def create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS triples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                predicate_id INTEGER NOT NULL,
                object_id INTEGER NOT NULL,
                object_type TEXT NOT NULL DEFAULT 'entity',
                event_id INTEGER NOT NULL,
                role TEXT NOT NULL DEFAULT '',
                context TEXT NOT NULL DEFAULT 'world',
                FOREIGN KEY (subject_id) REFERENCES entity_dict(id),
                FOREIGN KEY (predicate_id) REFERENCES predicate_dict(id)
            );
            CREATE INDEX IF NOT EXISTS idx_spo ON triples(subject_id, predicate_id, object_id);
            CREATE INDEX IF NOT EXISTS idx_pos ON triples(predicate_id, object_id, subject_id);
            CREATE INDEX IF NOT EXISTS idx_ops ON triples(object_id, predicate_id, subject_id);
            CREATE INDEX IF NOT EXISTS idx_event ON triples(event_id);
        """)
        if self._six_index:
            self._conn.executescript("""
                CREATE INDEX IF NOT EXISTS idx_sop ON triples(subject_id, object_id, predicate_id);
                CREATE INDEX IF NOT EXISTS idx_pso ON triples(predicate_id, subject_id, object_id);
                CREATE INDEX IF NOT EXISTS idx_osp ON triples(object_id, subject_id, predicate_id);
            """)

    def insert_triple(self, t: EncodedTriple) -> int:
        cur = self._conn.execute(
            """INSERT INTO triples(subject_id, predicate_id, object_id,
                                   object_type, event_id, role, context)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                t.subject_id,
                t.predicate_id,
                t.object_id,
                t.object_type,
                t.event_id,
                t.role,
                t.context,
            ),
        )
        return cur.lastrowid or 0

    def scan_spo(self, s: int | None, p: int | None, o: int | None) -> list[tuple]:
        parts: list[str] = []
        params: list[int] = []
        if s is not None:
            parts.append("subject_id = ?")
            params.append(s)
        if p is not None:
            parts.append("predicate_id = ?")
            params.append(p)
        if o is not None:
            parts.append("object_id = ?")
            params.append(o)
        where = " AND ".join(parts) if parts else "1=1"
        cur = self._conn.execute(
            f"SELECT subject_id, predicate_id, object_id, object_type, event_id, role, context, id FROM triples WHERE {where} ORDER BY id",
            params,
        )
        return cur.fetchall()

    def scan_event(self, event_id: int) -> list[tuple]:
        cur = self._conn.execute(
            "SELECT subject_id, predicate_id, object_id, object_type, event_id, role, context, id FROM triples WHERE event_id = ? ORDER BY id",
            (event_id,),
        )
        return cur.fetchall()

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM triples")
        return cur.fetchone()[0]

    def drop(self) -> None:
        self._conn.executescript("DROP TABLE IF EXISTS triples;")


# ---------------------------------------------------------------------------
# Knowledge Graph Engine
# ---------------------------------------------------------------------------


class KnowledgeGraphEngine(DatabaseEngine):
    """SQLite-backed RDF-style Knowledge Graph with dictionary encoding.

    This engine implements the full DatabaseEngine interface and serves
    as the reference baseline for all benchmarks.
    """

    def __init__(self, name: str = "kg_default") -> None:
        self._name = name
        self._conn: sqlite3.Connection | None = None
        self._encoder: DictionaryEncoder | None = None
        self._indexes: IndexManager | None = None
        self._hooks = BenchmarkHooks()
        self._db_path: str = ":memory:"
        self._six_index: bool = False
        self._initialized = False
        self._fact_count: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @property
    def engine_type(self) -> EngineType:
        return EngineType.KNOWLEDGE_GRAPH

    def create(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self._db_path = cfg.get("db_path", ":memory:")
        self._six_index = cfg.get("six_index", False)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._encoder = DictionaryEncoder(self._conn)
        self._encoder.create_tables()
        self._indexes = IndexManager(self._conn, self._six_index)
        self._indexes.create_tables()
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS reification (
                event_id INTEGER NOT NULL,
                fact_id TEXT NOT NULL,
                triple_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                PRIMARY KEY (event_id, triple_id)
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reification_event ON reification(event_id)
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS engine_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self._conn.execute(
            """
            INSERT OR IGNORE INTO engine_metadata(key, value) VALUES ('name', ?)
        """,
            (self._name,),
        )
        self._conn.execute("""
            INSERT OR IGNORE INTO engine_metadata(key, value) VALUES ('engine_type', 'kg')
        """)
        self._conn.execute(
            """
            INSERT OR IGNORE INTO engine_metadata(key, value) VALUES ('created_at', ?)
        """,
            (datetime.now(UTC).isoformat(),),
        )
        self._conn.commit()
        self._initialized = True

    def drop(self) -> None:
        if self._conn is None:
            return
        self._conn.executescript("""
            DROP TABLE IF EXISTS triples;
            DROP TABLE IF EXISTS entity_dict;
            DROP TABLE IF EXISTS predicate_dict;
            DROP TABLE IF EXISTS literal_table;
            DROP TABLE IF EXISTS reification;
            DROP TABLE IF EXISTS engine_metadata;
        """)
        self._conn.commit()
        self._conn.close()
        self._conn = None
        self._initialized = False

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def insert(self, fact: SemanticFact) -> InsertResult:
        t0 = time.perf_counter_ns()
        self._require_init()
        assert self._encoder is not None
        assert self._indexes is not None
        assert self._conn is not None
        try:
            event_eid = self._encoder.encode_entity(fact.id.value)
            subj_eid = self._encoder.encode_entity(fact.subject.value)
            rel_pid = self._encoder.encode_predicate(fact.relation.value)
            ctx_str = str(fact.context)

            # Build all triples for this fact via a data-driven schema
            triples: list[EncodedTriple] = []

            # Static metadata triples
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(RDF_TYPE), self._encoder.encode_entity(SFDB_FACT), OBJECT_TYPE_ENTITY, event_eid, "type", ctx_str))
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(RDF_SUBJECT), subj_eid, OBJECT_TYPE_ENTITY, event_eid, "subject", ctx_str))
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(RDF_PREDICATE), rel_pid, OBJECT_TYPE_ENTITY, event_eid, "predicate", ctx_str))

            # Object slots (n-ary)
            for i, obj in enumerate(fact.objects):
                oid, otype = self._encode_value(obj)
                triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(f"{RDF_OBJECT}_{i}"), oid, otype, event_eid, f"object_{i}", ctx_str))

            # Attributes
            for k, v in fact.attributes.items():
                aid, atype = self._encode_value(v)
                triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(f"{SFDB_ATTR_PREFIX}{k}"), aid, atype, event_eid, f"attr_{k}", ctx_str))

            # Context
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_CONTEXT), self._encoder.encode_literal(ctx_str), OBJECT_TYPE_LITERAL, event_eid, "context", ctx_str))

            # Confidence
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_CONFIDENCE), self._encoder.encode_literal(str(fact.confidence), "float"), OBJECT_TYPE_LITERAL, event_eid, "confidence", ctx_str))

            # Provenance
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_PROV_SOURCE), self._encoder.encode_literal(fact.provenance.source), OBJECT_TYPE_LITERAL, event_eid, "prov_source", ctx_str))
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_PROV_RECORDED), self._encoder.encode_literal(fact.provenance.recorded_at.isoformat(), "datetime"), OBJECT_TYPE_LITERAL, event_eid, "prov_recorded", ctx_str))
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_PROV_CONFIDENCE), self._encoder.encode_literal(str(fact.provenance.confidence), "float"), OBJECT_TYPE_LITERAL, event_eid, "prov_confidence", ctx_str))
            triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_PROV_METHOD), self._encoder.encode_literal(fact.provenance.method), OBJECT_TYPE_LITERAL, event_eid, "prov_method", ctx_str))

            # Temporal
            if fact.temporal is not None:
                if fact.temporal.start is not None:
                    triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_TEMPORAL_START), self._encoder.encode_literal(fact.temporal.start.isoformat(), "datetime"), OBJECT_TYPE_LITERAL, event_eid, "temporal_start", ctx_str))
                if fact.temporal.end is not None:
                    triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(SFDB_TEMPORAL_END), self._encoder.encode_literal(fact.temporal.end.isoformat(), "datetime"), OBJECT_TYPE_LITERAL, event_eid, "temporal_end", ctx_str))

            # Metadata
            for mk, mv in fact.metadata.items():
                mv_str = json.dumps(mv) if not isinstance(mv, str) else mv
                triples.append(EncodedTriple(event_eid, self._encoder.encode_predicate(f"sfdb:meta_{mk}"), self._encoder.encode_literal(mv_str), OBJECT_TYPE_LITERAL, event_eid, f"meta_{mk}", ctx_str))

            # Insert all triples
            for t in triples:
                self._indexes.insert_triple(t)

            self._conn.commit()
            self._fact_count += 1
            ns = time.perf_counter_ns() - t0
            self._hooks.record_insert(ns)
            return InsertResult(fact_id=fact.id, success=True)
        except Exception as exc:
            self._conn.rollback()
            return InsertResult(fact_id=fact.id, success=False, message=str(exc))

    def update(self, fact_id: Identifier, fact: SemanticFact) -> UpdateResult:
        t0 = time.perf_counter_ns()
        del_result = self.delete(fact_id)
        if not del_result.success:
            return UpdateResult(fact_id=fact_id, success=False, message=del_result.message)
        insert_result = self.insert(fact)
        time.perf_counter_ns() - t0
        return UpdateResult(
            fact_id=fact_id,
            success=insert_result.success,
            message=insert_result.message,
        )

    def delete(self, fact_id: Identifier) -> DeleteResult:
        self._require_init()
        assert self._conn is not None
        try:
            fact_id_str = fact_id.value
            cur = self._conn.execute("SELECT id FROM entity_dict WHERE name = ?", (fact_id_str,))
            row = cur.fetchone()
            if row is None:
                return DeleteResult(fact_id=fact_id, success=False, message="Fact not found")
            event_eid = row[0]
            self._conn.execute("DELETE FROM triples WHERE event_id = ?", (event_eid,))
            self._conn.execute("DELETE FROM reification WHERE event_id = ?", (event_eid,))
            self._conn.commit()
            return DeleteResult(fact_id=fact_id, success=True)
        except Exception as exc:
            self._conn.rollback()
            return DeleteResult(fact_id=fact_id, success=False, message=str(exc))

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, query: Query) -> QueryResult:
        t0 = time.perf_counter_ns()
        self._require_init()
        assert self._conn is not None
        assert self._encoder is not None
        try:
            facts = self._execute_query(query)
            ns = time.perf_counter_ns() - t0
            self._hooks.record_execution(ns)
            return QueryResult(
                facts=tuple(facts),
                execution_time_ns=ns,
                rows_scanned=len(facts),
            )
        except Exception as exc:
            raise QueryError(f"Query failed: {exc}") from exc

    def query_sparql(self, query_str: str) -> list[dict[str, str]]:
        from sfdb.kg.sparql import SparqlExecutor, parse_sparql

        try:
            parsed = parse_sparql(query_str)
            assert self._indexes is not None
            all_triples = self._indexes.scan_spo(None, None, None)
            executor = SparqlExecutor(all_triples)
            return executor.execute(parsed)
        except Exception:
            return []

    def _execute_query(self, query: Query) -> list[SemanticFact]:
        assert self._indexes is not None
        assert self._encoder is not None
        q = query
        event_ids: set[int] = set()

        if q.query_type == QueryType.LOOKUP and q.subject is not None:
            eid = self._encoder.encode_entity(q.subject.value)
            rows = self._indexes.scan_spo(s=eid, p=None, o=None)
            for r in rows:
                event_ids.add(r[4])

        elif q.query_type == QueryType.CONTEXT:
            ctx_str = q.context
            lit_id = self._encoder.encode_literal(ctx_str)
            pred_ctx = self._encoder.encode_predicate(SFDB_CONTEXT)
            rows = self._indexes.scan_spo(s=None, p=pred_ctx, o=lit_id)
            for r in rows:
                event_ids.add(r[4])

        elif q.query_type == QueryType.NEIGHBORHOOD and q.subject is not None:
            eid = self._encoder.encode_entity(q.subject.value)
            rows = self._indexes.scan_spo(s=eid, p=None, o=None)
            for r in rows:
                event_ids.add(r[4])
            rows2 = self._indexes.scan_spo(s=None, p=None, o=eid)
            for r in rows2:
                event_ids.add(r[4])

        elif q.query_type == QueryType.GLOBAL:
            cur = self._conn.execute("SELECT DISTINCT event_id FROM triples")
            for row in cur:
                event_ids.add(row[0])

        else:
            cur = self._conn.execute("SELECT DISTINCT event_id FROM triples LIMIT ?", (q.limit,))
            for row in cur:
                event_ids.add(row[0])

        if q.limit > 0 and len(event_ids) > q.limit:
            event_ids = set(list(event_ids)[: q.limit])

        result: list[SemanticFact] = []
        for eid in event_ids:
            fact = self._reconstruct_fact(eid)
            if fact is not None:
                result.append(fact)
        return result

    def _reconstruct_fact(self, event_eid: int) -> SemanticFact | None:
        assert self._encoder is not None
        assert self._indexes is not None
        rows = self._indexes.scan_event(event_eid)
        if not rows:
            return None

        fact_id_str: str | None = None
        subject_str: str | None = None
        relation_str: str | None = None
        objects: list[Value] = []
        attributes: dict[str, Value] = {}
        context_str: str = "world"
        confidence: float = 1.0
        prov_source: str = "unknown"
        prov_recorded: str | None = None
        prov_confidence: float = 1.0
        prov_method: str = "unknown"
        temporal_start: str | None = None
        temporal_end: str | None = None
        metadata: dict[str, Any] = {}

        for r in rows:
            _subj, pp, oo, otype, _ev, _role = r[0], r[1], r[2], r[3], r[4], r[5]
            pname = self._encoder.decode_predicate(pp)
            if pname is None:
                continue
            if pname == RDF_TYPE:
                fact_id_str = self._encoder.decode_entity(_subj)
            elif pname == RDF_SUBJECT:
                subject_str = self._encoder.decode_entity(oo)
            elif pname == RDF_PREDICATE:
                relation_str = self._encoder.decode_predicate(oo)
            elif pname.startswith(RDF_OBJECT):
                if otype == OBJECT_TYPE_ENTITY:
                    ename = self._encoder.decode_entity(oo)
                    if ename is not None:
                        objects.append(Value.reference(Identifier(ename)))
                else:
                    lit_val, lit_type = self._encoder.decode_literal(oo) or ("", "string")
                    objects.append(self._parse_literal(lit_val, lit_type))
            elif pname.startswith(SFDB_ATTR_PREFIX):
                k = pname[len(SFDB_ATTR_PREFIX) :]
                if otype == OBJECT_TYPE_ENTITY:
                    ename = self._encoder.decode_entity(oo)
                    if ename is not None:
                        attributes[k] = Value.reference(Identifier(ename))
                else:
                    lit_val, lit_type = self._encoder.decode_literal(oo) or ("", "string")
                    attributes[k] = self._parse_literal(lit_val, lit_type)
            elif pname == SFDB_CONTEXT:
                lit_val, _ = self._encoder.decode_literal(oo) or ("world", "string")
                context_str = lit_val
            elif pname == SFDB_CONFIDENCE:
                lit_val, _ = self._encoder.decode_literal(oo) or ("1.0", "float")
                confidence = float(lit_val)
            elif pname == SFDB_PROV_SOURCE:
                lit_val, _ = self._encoder.decode_literal(oo) or ("unknown", "string")
                prov_source = lit_val
            elif pname == SFDB_PROV_RECORDED:
                lit_val, _ = self._encoder.decode_literal(oo) or ("", "datetime")
                prov_recorded = lit_val
            elif pname == SFDB_PROV_CONFIDENCE:
                lit_val, _ = self._encoder.decode_literal(oo) or ("1.0", "float")
                prov_confidence = float(lit_val)
            elif pname == SFDB_PROV_METHOD:
                lit_val, _ = self._encoder.decode_literal(oo) or ("unknown", "string")
                prov_method = lit_val
            elif pname == SFDB_TEMPORAL_START:
                lit_val, _ = self._encoder.decode_literal(oo) or ("", "datetime")
                temporal_start = lit_val
            elif pname == SFDB_TEMPORAL_END:
                lit_val, _ = self._encoder.decode_literal(oo) or ("", "datetime")
                temporal_end = lit_val
            elif pname.startswith("sfdb:meta_"):
                k = pname[len("sfdb:meta_") :]
                lit_val, _ = self._encoder.decode_literal(oo) or ("", "string")
                try:
                    metadata[k] = json.loads(lit_val)
                except (json.JSONDecodeError, TypeError):
                    metadata[k] = lit_val

        if fact_id_str is None or subject_str is None or relation_str is None:
            return None

        prov = Provenance(
            source=prov_source,
            confidence=prov_confidence,
            method=prov_method,
        )
        if prov_recorded is not None:
            object.__setattr__(prov, "recorded_at", datetime.fromisoformat(prov_recorded))

        temporal: TemporalInfo | None = None
        if temporal_start is not None or temporal_end is not None:
            ts = datetime.fromisoformat(temporal_start) if temporal_start else None
            te = datetime.fromisoformat(temporal_end) if temporal_end else None
            temporal = TemporalInfo(start=ts, end=te)

        obj_tuple = tuple(objects)
        return SemanticFact(
            id=Identifier(fact_id_str),
            subject=Identifier(subject_str),
            relation=Identifier(relation_str),
            objects=obj_tuple,
            attributes=attributes,
            context=Context(context_str),
            provenance=prov,
            confidence=confidence,
            temporal=temporal,
            metadata=metadata,
        )

    def _parse_literal(self, val: str, typ: str) -> Value:
        if typ == "int":
            return Value.literal(int(val))
        if typ == "float":
            return Value.literal(float(val))
        if typ == "bool":
            return Value.literal(val.lower() == "true")
        if typ == "quantity":
            try:
                return Value.literal(float(val))
            except ValueError:
                return Value.literal(int(val))
        return Value.literal(val)

    def _encode_value(self, v: Value) -> tuple[int, str]:
        """Encode a Value to (encoded_id, object_type)."""
        if v.is_reference:
            return self._encoder.encode_entity(str(v.inner)), OBJECT_TYPE_ENTITY
        return self._encoder.encode_literal(str(v.inner), v.type_hint.name.lower()), OBJECT_TYPE_LITERAL

    def explain(self, query: Query) -> ExecutionPlan:
        t0 = time.perf_counter_ns()
        q = query
        steps: list[str] = [
            f"IndexScan: lookup_type={q.query_type.name}",
            f"Filter: subject={q.subject}, relation={q.relation}",
        ]
        if q.limit > 0:
            steps.append(f"Limit: {q.limit}")
        if q.context != "world":
            steps.append(f"ContextFilter: {q.context}")
        time.perf_counter_ns() - t0
        return ExecutionPlan(
            description=f"KG plan for {q.query_type.name}",
            estimated_cost=len(steps) * 1.0,
            steps=tuple(steps),
        )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def statistics(self) -> EngineStatistics:
        self._require_init()
        assert self._encoder is not None
        assert self._indexes is not None
        entity_count = self._encoder.entity_count()
        predicate_count = self._encoder.predicate_count()
        literal_count = self._encoder.literal_count()
        triple_count = self._indexes.count()

        # Collect selectivity statistics
        selectivity: dict[str, float] = {}
        selectivity["triple_count"] = float(triple_count)
        selectivity["entity_count"] = float(entity_count)
        selectivity["predicate_count"] = float(predicate_count)
        selectivity["avg_facts_per_entity"] = triple_count / max(1, entity_count)
        selectivity["avg_triples_per_fact"] = triple_count / max(1, self._fact_count)

        return EngineStatistics(
            total_facts=triple_count,
            total_entities=entity_count + predicate_count + literal_count,
            storage_bytes=self._estimate_storage_bytes(),
            index_count=4 if not self._six_index else 7,
            engine_type=EngineType.KNOWLEDGE_GRAPH,
            selectivity=selectivity,
        )

    def _estimate_storage_bytes(self) -> int:
        assert self._conn is not None
        if self._db_path == ":memory:":
            cur = self._conn.execute(
                "SELECT page_count * page_size FROM pragma_page_count, pragma_page_size"
            )
            row = cur.fetchone()
            return row[0] if row else 0
        path = Path(self._db_path)
        return path.stat().st_size if path.exists() else 0

    def verify(self) -> VerificationResult:
        self._require_init()
        assert self._conn is not None
        errors: list[str] = []
        cur = self._conn.execute(
            "SELECT COUNT(*) FROM triples t LEFT JOIN entity_dict e ON t.subject_id = e.id WHERE e.id IS NULL"
        )
        if cur.fetchone()[0] > 0:
            errors.append("Orphan triples: subject_id missing from entity_dict")
        cur = self._conn.execute(
            "SELECT COUNT(*) FROM triples t LEFT JOIN predicate_dict p ON t.predicate_id = p.id WHERE p.id IS NULL"
        )
        if cur.fetchone()[0] > 0:
            errors.append("Orphan triples: predicate_id missing from predicate_dict")
        return VerificationResult(valid=len(errors) == 0, errors=tuple(errors))

    # ------------------------------------------------------------------
    # Bulk
    # ------------------------------------------------------------------

    def export(self, fmt: StorageFormat = StorageFormat.JSON) -> bytes:
        self._require_init()
        all_facts = self._execute_query(Query(query_type=QueryType.GLOBAL, limit=0))
        if fmt == StorageFormat.JSON:
            return serialize_json(all_facts)
        if fmt == StorageFormat.MSGPACK:
            return serialize_msgpack(all_facts)
        raise ValueError(f"Unsupported format: {fmt}")

    def import_data(self, data: bytes, fmt: StorageFormat = StorageFormat.JSON) -> int:
        if fmt == StorageFormat.JSON:
            facts = deserialize_json(data)
        elif fmt == StorageFormat.MSGPACK:
            facts = deserialize_msgpack(data)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
        count = 0
        for fact in facts:
            result = self.insert(fact)
            if result.success:
                count += 1
        return count

    # ------------------------------------------------------------------
    # Benchmark hooks
    # ------------------------------------------------------------------

    def benchmark_stats(self) -> dict[str, Any]:
        h = self._hooks
        return {
            "insert_count": len(h.insert_times),
            "insert_avg_ns": sum(h.insert_times) / len(h.insert_times) if h.insert_times else 0,
            "insert_max_ns": max(h.insert_times) if h.insert_times else 0,
            "insert_min_ns": min(h.insert_times) if h.insert_times else 0,
            "lookup_count": len(h.lookup_times),
            "lookup_avg_ns": sum(h.lookup_times) / len(h.lookup_times) if h.lookup_times else 0,
            "execution_count": len(h.execution_times),
            "execution_avg_ns": sum(h.execution_times) / len(h.execution_times)
            if h.execution_times
            else 0,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_init(self) -> None:
        if not self._initialized:
            raise StorageError("KnowledgeGraphEngine not initialized. Call create() first.")
