"""Central registry of all known optimization modules.

Each module is registered with:
  - name: machine-readable identifier
  - description: human-readable summary
  - engine: 'sheaf' | 'kg' | 'general'
  - default_on: whether the optimization is active by default
  - dependencies: list of other optimization names this depends on
  - category: 'cache' | 'index' | 'algorithm' | 'storage' | 'execution'

The registry is populated by importing the module definitions.
Code that needs to know about available optimizations imports
OptimizationRegistry and iterates over registered entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class OptimizationEntry:
    name: str
    description: str
    engine: str  # "sheaf" | "kg" | "general"
    default_on: bool = True
    dependencies: tuple[str, ...] = ()
    category: str = "execution"
    parameters: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"


class OptimizationRegistry:
    _entries: dict[str, OptimizationEntry] = {}
    _initialized = False

    @classmethod
    def register(cls, entry: OptimizationEntry) -> None:
        if entry.name in cls._entries:
            raise ValueError(f"Optimization '{entry.name}' already registered")
        cls._entries[entry.name] = entry

    @classmethod
    def get(cls, name: str) -> OptimizationEntry | None:
        return cls._entries.get(name)

    @classmethod
    def all(cls) -> list[OptimizationEntry]:
        return list(cls._entries.values())

    @classmethod
    def by_engine(cls, engine: str) -> list[OptimizationEntry]:
        return [e for e in cls._entries.values() if e.engine == engine]

    @classmethod
    def by_category(cls, category: str) -> list[OptimizationEntry]:
        return [e for e in cls._entries.values() if e.category == category]

    @classmethod
    def count(cls) -> int:
        return len(cls._entries)

    @classmethod
    def names(cls) -> list[str]:
        return list(cls._entries.keys())

    @classmethod
    def reset(cls) -> None:
        cls._entries.clear()
        cls._initialized = False

    @classmethod
    def initialize_defaults(cls) -> None:
        if cls._initialized:
            return

        # ── Sheaf optimizations ──────────────────────────────────────
        sheaf_opts: list[OptimizationEntry] = [
            OptimizationEntry(
                name="sheaf.restriction_cache",
                description="Cache restriction map results (keyed by source→target open set pair)",
                engine="sheaf",
                default_on=True,
                category="cache",
            ),
            OptimizationEntry(
                name="sheaf.global_section_cache",
                description="Cache computed global sections to avoid recomputing on repeated queries",
                engine="sheaf",
                default_on=True,
                category="cache",
            ),
            OptimizationEntry(
                name="sheaf.neighborhood_index",
                description="Entity adjacency index for O(1) neighborhood queries",
                engine="sheaf",
                default_on=True,
                category="index",
            ),
            OptimizationEntry(
                name="sheaf.context_index",
                description="Map context strings to fact IDs for fast context-scoped queries",
                engine="sheaf",
                default_on=True,
                category="index",
            ),
            OptimizationEntry(
                name="sheaf.temporal_index",
                description="Year-based temporal index for range queries",
                engine="sheaf",
                default_on=True,
                category="index",
            ),
            OptimizationEntry(
                name="sheaf.provenance_index",
                description="Source/method provenance index for provenance-scoped queries",
                engine="sheaf",
                default_on=True,
                category="index",
            ),
            OptimizationEntry(
                name="sheaf.topology_compression",
                description="Collapse open sets with identical sections to reduce topology size",
                engine="sheaf",
                default_on=False,
                category="storage",
                parameters={"min_shared": 0.8},
            ),
            OptimizationEntry(
                name="sheaf.lazy_restriction",
                description="Defer restriction computation until results are actually accessed",
                engine="sheaf",
                default_on=False,
                category="execution",
            ),
            OptimizationEntry(
                name="sheaf.stalk_prefetch",
                description="Prefetch stalks likely to be queried based on access patterns",
                engine="sheaf",
                default_on=False,
                category="execution",
            ),
            OptimizationEntry(
                name="sheaf.section_dedup",
                description="Deduplicate sections with identical fact content across open sets",
                engine="sheaf",
                default_on=False,
                category="storage",
            ),
            OptimizationEntry(
                name="sheaf.parallel_gluing",
                description="Parallelise global section computation across open set pairs",
                engine="sheaf",
                default_on=False,
                category="execution",
                parameters={"max_workers": 4},
            ),
            OptimizationEntry(
                name="sheaf.context_aware_gluing",
                description="Only glue sections that share a context filter",
                engine="sheaf",
                default_on=False,
                category="algorithm",
            ),
            OptimizationEntry(
                name="sheaf.incremental_update",
                description="Update global sections incrementally on insert instead of full recompute",
                engine="sheaf",
                default_on=False,
                category="algorithm",
            ),
        ]
        for opt in sheaf_opts:
            cls.register(opt)

        # ── KG optimizations ──────────────────────────────────────────
        kg_opts: list[OptimizationEntry] = [
            OptimizationEntry(
                name="kg.six_index",
                description="Six-way SPO/POS/OPS/SOP/PSO/OSP indexes for all pattern access paths",
                engine="kg",
                default_on=False,
                category="index",
            ),
            OptimizationEntry(
                name="kg.dictionary_encoding",
                description="Encode strings as integers to reduce storage and comparison cost",
                engine="kg",
                default_on=True,
                category="storage",
            ),
            OptimizationEntry(
                name="kg.dictionary_cache",
                description="In-memory cache of dictionary lookups (entity/predicate/literal)",
                engine="kg",
                default_on=True,
                category="cache",
            ),
            OptimizationEntry(
                name="kg.predicate_partitioning",
                description="Partition triples by predicate for faster predicate-scoped scans",
                engine="kg",
                default_on=False,
                category="storage",
            ),
            OptimizationEntry(
                name="kg.join_reordering",
                description="Reorder hash joins by estimated cardinality",
                engine="kg",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="kg.filter_pushdown",
                description="Push selection filters closer to scan nodes",
                engine="kg",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="kg.batch_insert",
                description="Batch inserts into a single transaction to reduce commit overhead",
                engine="kg",
                default_on=True,
                category="execution",
            ),
            OptimizationEntry(
                name="kg.pragma_tuning",
                description="Set SQLite PRAGMAs (journal_mode=WAL, synchronous=NORMAL) for performance",
                engine="kg",
                default_on=True,
                category="execution",
            ),
            OptimizationEntry(
                name="kg.reification_skip",
                description="Skip reconstruction of unused reification triples during query",
                engine="kg",
                default_on=True,
                category="execution",
            ),
            OptimizationEntry(
                name="kg.result_caching",
                description="Cache query results by normalized query text",
                engine="kg",
                default_on=False,
                category="cache",
            ),
        ]
        for opt in kg_opts:
            cls.register(opt)

        # ── Query-level optimizations ──────────────────────────────────
        query_opts: list[OptimizationEntry] = [
            OptimizationEntry(
                name="query.lru_parsed_cache",
                description="LRU cache of parsed AST by query text hash",
                engine="general",
                default_on=True,
                category="cache",
            ),
            OptimizationEntry(
                name="query.lru_logical_cache",
                description="LRU cache of logical plans by AST hash",
                engine="general",
                default_on=True,
                category="cache",
                dependencies=("query.lru_parsed_cache",),
            ),
            OptimizationEntry(
                name="query.lru_physical_cache",
                description="LRU cache of physical plans by logical plan hash",
                engine="general",
                default_on=True,
                category="cache",
                dependencies=("query.lru_logical_cache",),
            ),
            OptimizationEntry(
                name="query.constant_folding",
                description="Evaluate constant expressions at planning time",
                engine="general",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="query.predicate_pushdown",
                description="Move predicates closer to scan operators",
                engine="general",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="query.projection_pushdown",
                description="Remove unused columns early in the plan",
                engine="general",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="query.dead_operator_removal",
                description="Remove operators that produce no results (e.g., LIMIT 0)",
                engine="general",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="query.logical_simplification",
                description="Simplify redundant projections and selections",
                engine="general",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="query.cost_optimizer",
                description="Select optimal engine (KG vs Sheaf) based on cost model",
                engine="general",
                default_on=True,
                category="algorithm",
            ),
            OptimizationEntry(
                name="query.result_caching",
                description="Cache final query results by normalized query + engine fingerprint",
                engine="general",
                default_on=False,
                category="cache",
            ),
        ]
        for opt in query_opts:
            cls.register(opt)

        cls._initialized = True

    @classmethod
    def summary(cls) -> str:
        lines = ["Optimization Registry Summary", "=" * 80]
        by_eng: dict[str, list[OptimizationEntry]] = {}
        for e in cls._entries.values():
            by_eng.setdefault(e.engine, []).append(e)
        for engine in sorted(by_eng):
            entries = by_eng[engine]
            lines.append(f"\n{engine.upper()} ({len(entries)} optimizations):")
            lines.append("-" * 60)
            for e in sorted(entries, key=lambda x: x.name):
                on_off = "ON " if e.default_on else "OFF"
                lines.append(f"  [{on_off}] {e.name:45s}  [{e.category}]  {e.description}")
        return "\n".join(lines)

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            name: {
                "engine": entry.engine,
                "default_on": entry.default_on,
                "category": entry.category,
                "dependencies": list(entry.dependencies),
                "description": entry.description,
            }
            for name, entry in cls._entries.items()
        }
