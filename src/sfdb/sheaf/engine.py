"""SheafDatabaseEngine — a sheaf-native semantic database.

This engine implements the DatabaseEngine ABC using finite sheaf
theory as its primary storage model.

Key difference from the KnowledgeGraphEngine:
- Facts are stored as complete LocalSections, NOT decomposed into
  triples.
- The storage hierarchy is: TopologicalSpace → OpenSets → Stalks →
  LocalSections → RestrictionMaps → GlobalSections.
- Query execution uses restriction operations rather than graph
  traversals.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson as orjson

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
    StorageFormat,
    UpdateResult,
    VerificationResult,
)
from common.schema import SemanticFact
from common.serialization import (
    _dict_to_fact,
    _fact_to_dict,
    deserialize_json,
    serialize_json,
)
from common.types import Identifier
from sfdb.sheaf.builder import TopologyBuilder, TopologyStrategy
from sfdb.sheaf.consistency import ConsistencyChecker
from sfdb.sheaf.indexes import (
    ContextIndex,
    GlobalSectionCache,
    NeighborhoodIndex,
    OpenSetIndex,
    ProvenanceIndex,
    RestrictionIndex,
    StalkIndex,
    TemporalIndex,
)
from sfdb.sheaf.optimizer import SheafOptimizer
from sfdb.sheaf.presheaf import LocalSection, Presheaf, Sheaf
from sfdb.sheaf.query import SheafQueryPlanner
from sfdb.sheaf.restriction import RestrictionGraph
from sfdb.sheaf.topology import FiniteTopologicalSpace, OpenSet


@dataclass
class SheafBenchmarkHooks:
    """Benchmark instrumentation for the sheaf database."""

    construction_times: list[float] = field(default_factory=list)
    restriction_times: list[float] = field(default_factory=list)
    global_section_times: list[float] = field(default_factory=list)
    local_query_times: list[float] = field(default_factory=list)
    semilocal_query_times: list[float] = field(default_factory=list)
    global_query_times: list[float] = field(default_factory=list)
    consistency_check_times: list[float] = field(default_factory=list)
    memory_samples: list[int] = field(default_factory=list)

    def record_construction(self, ns: float) -> None:
        self.construction_times.append(ns)

    def record_restriction(self, ns: float) -> None:
        self.restriction_times.append(ns)

    def record_global_section(self, ns: float) -> None:
        self.global_section_times.append(ns)

    def record_local_query(self, ns: float) -> None:
        self.local_query_times.append(ns)

    def record_semilocal_query(self, ns: float) -> None:
        self.semilocal_query_times.append(ns)

    def record_global_query(self, ns: float) -> None:
        self.global_query_times.append(ns)

    def record_consistency(self, ns: float) -> None:
        self.consistency_check_times.append(ns)


class SheafDatabaseEngine(DatabaseEngine):
    """A sheaf-native semantic database.

    Stores each SemanticFact as a complete LocalSection in the
    appropriate stalk(s), indexed by open set membership.  The
    topology is built automatically from the facts themselves.
    """

    def __init__(self, name: str = "sheaf_default") -> None:
        self._name = name
        self._conn: sqlite3.Connection | None = None
        self._topology = FiniteTopologicalSpace()
        self._presheaf: Presheaf | None = None
        self._openset_index = OpenSetIndex()
        self._stalk_index = StalkIndex()
        self._restriction_index = RestrictionIndex()
        self._context_index = ContextIndex()
        self._neighborhood_index = NeighborhoodIndex()
        self._temporal_index = TemporalIndex()
        self._provenance_index = ProvenanceIndex()
        self._global_section_cache = GlobalSectionCache()
        self._restriction_graph = RestrictionGraph()
        self._optimizer: SheafOptimizer | None = None
        self._planner: SheafQueryPlanner | None = None
        self._hooks = SheafBenchmarkHooks()
        self._db_path: str = ":memory:"
        self._initialized = False
        self._fact_count = 0

    @property
    def engine_type(self) -> EngineType:
        return EngineType.SHEAF_DATABASE

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or {}
        self._db_path = cfg.get("db_path", ":memory:")

        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._create_sqlite_tables()

        self._topology = FiniteTopologicalSpace()
        self._topology.name = self._name
        empty_set = OpenSet("∅", frozenset())
        self._topology.add_open_set(empty_set)
        universe = OpenSet("𝕌", frozenset())
        self._topology.add_open_set(universe)

        self._presheaf = Sheaf(self._topology)
        self._optimizer = SheafOptimizer(
            openset_index=self._openset_index,
            context_index=self._context_index,
            neighborhood_index=self._neighborhood_index,
            temporal_index=self._temporal_index,
            provenance_index=self._provenance_index,
            restriction_graph=self._restriction_graph,
        )
        self._planner = SheafQueryPlanner(
            presheaf=self._presheaf,
            optimizer=self._optimizer,
            cache=self._global_section_cache,
            restriction_graph=self._restriction_graph,
        )
        self._initialized = True

    def _create_sqlite_tables(self) -> None:
        assert self._conn is not None
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sections (
                fact_id TEXT PRIMARY KEY,
                json_data TEXT NOT NULL,
                open_set_name TEXT NOT NULL,
                context TEXT NOT NULL DEFAULT 'world',
                subject TEXT NOT NULL DEFAULT '',
                relation TEXT NOT NULL DEFAULT '',
                provenance_source TEXT NOT NULL DEFAULT 'unknown',
                temporal_year TEXT DEFAULT NULL,
                confidence REAL DEFAULT 1.0,
                inserted_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_sections_openset ON sections(open_set_name);
            CREATE INDEX IF NOT EXISTS idx_sections_subject ON sections(subject);
            CREATE INDEX IF NOT EXISTS idx_sections_context ON sections(context);
            CREATE INDEX IF NOT EXISTS idx_sections_relation ON sections(relation);
            CREATE TABLE IF NOT EXISTS topology_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS restriction_maps (
                source_name TEXT NOT NULL,
                target_name TEXT NOT NULL,
                application_count INTEGER DEFAULT 0,
                PRIMARY KEY (source_name, target_name)
            );
        """)

    def drop(self) -> None:
        if self._conn is not None:
            self._conn.executescript("""
                DROP TABLE IF EXISTS sections;
                DROP TABLE IF EXISTS topology_metadata;
                DROP TABLE IF EXISTS restriction_maps;
            """)
            self._conn.close()
            self._conn = None
        self._topology = FiniteTopologicalSpace()
        self._presheaf = None
        self._initialized = False
        self._fact_count = 0

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def insert(self, fact: SemanticFact) -> InsertResult:
        t0 = time.perf_counter_ns()
        self._require_init()

        try:
            # Incremental topology — avoid O(N) fact reload + O(N·|tau|²) rebuild
            os_names = self._assign_open_sets(fact)

            # Add the point to the universe set
            self._topology.add_point_to_open_set("𝕌", fact.id.value)

            # Create event singleton and add to all relevant open sets
            for os_name in os_names:
                self._topology.add_point_to_open_set(os_name, fact.id.value)

                section = LocalSection(fact=fact, open_set_name=os_name)
                assert self._presheaf is not None
                self._presheaf.assign(section)
                self._openset_index.add(os_name, fact.id.value)

                stalk = self._stalk_index.get_or_create(fact.id.value)
                stalk.add_section(section)

            self._context_index.add(str(fact.context), fact.id.value)
            self._neighborhood_index.index_fact(fact)
            self._temporal_index.index_fact(fact)
            self._provenance_index.index_fact(fact)

            self._persist_section(fact, os_names)

            self._fact_count += 1
            self._global_section_cache.invalidate()

            ns = time.perf_counter_ns() - t0
            self._hooks.record_construction(ns)
            return InsertResult(fact_id=fact.id, success=True)
        except Exception as exc:
            return InsertResult(fact_id=fact.id, success=False, message=str(exc))

    def _assign_open_sets(self, fact: SemanticFact) -> list[str]:
        """Determine which open sets a fact belongs to."""
        names: list[str] = [f"event:{fact.id.value}"]
        names.append(f"entity:{fact.subject.value}")
        for obj in fact.objects:
            if obj.is_reference and obj.inner is not None:
                names.append(f"entity:{obj.inner!s}")
        if fact.temporal is not None and fact.temporal.start is not None:
            names.append(f"temporal:{fact.temporal.start.year}")
        else:
            names.append("temporal:atemporal")
        ctx_str = str(fact.context)
        names.append(f"context:{ctx_str}")
        parts = ctx_str.split(".")
        for i in range(1, len(parts)):
            names.append(f"context:{'.'.join(parts[:i])}")
        names.append(f"provenance:source:{fact.provenance.source}")
        names.append(f"provenance:method:{fact.provenance.method}")
        return names

    def _build_restriction_edges(self) -> None:
        if not self._topology.is_restriction_dirty:
            return
        os_list = list(self._topology._open_sets.values())
        for u in os_list:
            for v in os_list:
                if u.name != v.name and v.is_subset_of(u) and v.points:
                    self._restriction_graph.add_edge(u.name, v.name)
        self._topology.mark_restriction_clean()

    def _persist_section(self, fact: SemanticFact, os_names: list[str]) -> None:
        assert self._conn is not None
        json_data = serialize_json(fact).decode("utf-8")
        ctx_str = str(fact.context)
        year = None
        if fact.temporal is not None and fact.temporal.start is not None:
            year = str(fact.temporal.start.year)
        for os_name in os_names:
            self._conn.execute(
                """INSERT OR REPLACE INTO sections
                   (fact_id, json_data, open_set_name, context, subject, relation,
                    provenance_source, temporal_year, confidence, inserted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    fact.id.value,
                    json_data,
                    os_name,
                    ctx_str,
                    fact.subject.value,
                    fact.relation.value,
                    fact.provenance.source,
                    year,
                    fact.confidence,
                    datetime.now(UTC).isoformat(),
                ),
            )
        self._conn.commit()

    def update(self, fact_id: Identifier, fact: SemanticFact) -> UpdateResult:
        del_result = self.delete(fact_id)
        if not del_result.success:
            return UpdateResult(fact_id=fact_id, success=False, message=del_result.message)
        insert_result = self.insert(fact)
        return UpdateResult(
            fact_id=fact_id,
            success=insert_result.success,
            message=insert_result.message,
        )

    def delete(self, fact_id: Identifier) -> DeleteResult:
        self._require_init()
        assert self._conn is not None
        try:
            fid = fact_id.value
            self._conn.execute("DELETE FROM sections WHERE fact_id = ?", (fid,))
            self._conn.commit()

            self._openset_index.remove(fid)
            self._stalk_index.remove(fid)
            self._context_index.remove(fid)
            self._neighborhood_index.remove(fid)
            if self._presheaf is not None:
                for os_name in list(self._presheaf._sections_by_openset.keys()):
                    self._presheaf._sections_by_openset[os_name].pop(fid, None)
            self._global_section_cache.invalidate()
            self._fact_count = max(0, self._fact_count - 1)
            return DeleteResult(fact_id=fact_id, success=True)
        except Exception as exc:
            return DeleteResult(fact_id=fact_id, success=False, message=str(exc))

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, query: Query) -> QueryResult:
        self._require_init()
        assert self._planner is not None
        self._build_restriction_edges()
        t0 = time.perf_counter_ns()
        try:
            plan = self._planner.plan(query)
            result = self._planner.execute(plan, query)
            ns = time.perf_counter_ns() - t0
            if plan.classification.level == "local":
                self._hooks.record_local_query(ns)
            elif plan.classification.level == "semi_local":
                self._hooks.record_semilocal_query(ns)
            else:
                self._hooks.record_global_query(ns)
            return result
        except Exception as exc:
            raise QueryError(f"Sheaf query failed: {exc}") from exc

    def explain(self, query: Query) -> ExecutionPlan:
        self._require_init()
        assert self._planner is not None
        plan = self._planner.plan(query)
        steps = [str(s) for s in plan.steps]
        return ExecutionPlan(
            description=f"Sheaf plan ({plan.classification.level})",
            estimated_cost=plan.estimated_cost,
            steps=tuple(steps),
        )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def statistics(self) -> EngineStatistics:
        self._require_init()
        assert self._conn is not None
        cur = self._conn.execute("SELECT COUNT(*) FROM sections")
        total_sections = cur.fetchone()[0]

        # Collect selectivity statistics
        context_count = len(self._context_index._ctx_to_facts) if hasattr(self._context_index, '_ctx_to_facts') else 0
        selectivity: dict[str, float] = {}
        selectivity["section_count"] = float(total_sections)
        selectivity["fact_count"] = float(self._fact_count)
        selectivity["context_count"] = float(max(1, context_count))
        selectivity["avg_sections_per_context"] = total_sections / max(1, context_count)
        selectivity["avg_sections_per_fact"] = total_sections / max(1, self._fact_count)
        selectivity["open_set_count"] = float(self._topology.open_set_count())

        storage_bytes = 0
        if self._db_path != ":memory:":
            p = Path(self._db_path)
            storage_bytes = p.stat().st_size if p.exists() else 0
        else:
            cur = self._conn.execute(
                "SELECT page_count * page_size FROM pragma_page_count, pragma_page_size"
            )
            row = cur.fetchone()
            storage_bytes = row[0] if row else 0

        return EngineStatistics(
            total_facts=self._fact_count,
            total_entities=total_sections,
            storage_bytes=storage_bytes,
            index_count=8,
            engine_type=EngineType.SHEAF_DATABASE,
            selectivity=selectivity,
        )

    def verify(self) -> VerificationResult:
        self._require_init()
        assert self._presheaf is not None
        self._topology.intersection_closure()
        checker = ConsistencyChecker(self._presheaf, self._topology)
        results = checker.check_all()
        errors: list[str] = []
        for r in results:
            if not r.passed:
                errors.append(f"{r.check_name}: {r.detail}")
        if not errors:
            assert self._conn is not None
            cur = self._conn.execute("SELECT COUNT(*) FROM sections")
            db_count = cur.fetchone()[0]
            if db_count != self._fact_count:
                errors.append(f"Section count mismatch: DB={db_count}, index={self._fact_count}")
        return VerificationResult(valid=len(errors) == 0, errors=tuple(errors))

    # ------------------------------------------------------------------
    # Bulk
    # ------------------------------------------------------------------

    def export(self, fmt: StorageFormat = StorageFormat.JSON) -> bytes:
        self._require_init()
        facts = self._load_facts()
        if fmt == StorageFormat.JSON:
            dicts = [_fact_to_dict(f) for f in facts]
            return orjson.dumps(dicts, option=orjson.OPT_SORT_KEYS)
        raise ValueError(f"Unsupported format: {fmt}")

    def import_data(self, data: bytes, fmt: StorageFormat = StorageFormat.JSON) -> int:
        if fmt == StorageFormat.JSON:
            raw = orjson.loads(data)
            if isinstance(raw, dict):
                facts = [_dict_to_fact(raw)]
            else:
                facts = [_dict_to_fact(d) for d in raw]
        else:
            raise ValueError(f"Unsupported format: {fmt}")
        count = 0
        for fact in facts:
            result = self.insert(fact)
            if result.success:
                count += 1
        return count

    def _load_facts(self) -> list[SemanticFact]:
        assert self._conn is not None
        cur = self._conn.execute("SELECT DISTINCT fact_id, json_data FROM sections")
        seen: set[str] = set()
        facts: list[SemanticFact] = []
        for row in cur:
            fid = row[0]
            if fid not in seen:
                seen.add(fid)
                try:
                    loaded = deserialize_json(row[1].encode("utf-8"))
                    if isinstance(loaded, SemanticFact):
                        facts.append(loaded)
                except Exception:
                    pass
        return facts

    # ------------------------------------------------------------------
    # Benchmark hooks
    # ------------------------------------------------------------------

    def benchmark_stats(self) -> dict[str, Any]:
        h = self._hooks
        d = {
            "construction_count": len(h.construction_times),
            "construction_avg_ns": sum(h.construction_times) / len(h.construction_times)
            if h.construction_times
            else 0,
            "restriction_count": len(h.restriction_times),
            "restriction_avg_ns": sum(h.restriction_times) / len(h.restriction_times)
            if h.restriction_times
            else 0,
            "global_section_count": len(h.global_section_times),
            "global_section_avg_ns": sum(h.global_section_times) / len(h.global_section_times)
            if h.global_section_times
            else 0,
            "local_query_count": len(h.local_query_times),
            "local_query_avg_ns": sum(h.local_query_times) / len(h.local_query_times)
            if h.local_query_times
            else 0,
            "semilocal_query_count": len(h.semilocal_query_times),
            "semilocal_query_avg_ns": sum(h.semilocal_query_times) / len(h.semilocal_query_times)
            if h.semilocal_query_times
            else 0,
            "global_query_count": len(h.global_query_times),
            "global_query_avg_ns": sum(h.global_query_times) / len(h.global_query_times)
            if h.global_query_times
            else 0,
            "consistency_check_count": len(h.consistency_check_times),
            "consistency_check_avg_ns": sum(h.consistency_check_times)
            / len(h.consistency_check_times)
            if h.consistency_check_times
            else 0,
            "cache_hit_rate": self._optimizer.cache_hit_rate() if self._optimizer else 0.0,
        }
        return d

    # ------------------------------------------------------------------
    # Public accessors for testing
    # ------------------------------------------------------------------

    @property
    def topology(self) -> FiniteTopologicalSpace:
        return self._topology

    @property
    def presheaf(self) -> Presheaf | None:
        return self._presheaf

    @property
    def global_section_cache(self) -> GlobalSectionCache:
        return self._global_section_cache

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_init(self) -> None:
        if not self._initialized:
            raise StorageError("SheafDatabaseEngine not initialized. Call create() first.")
