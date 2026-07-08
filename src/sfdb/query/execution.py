"""Query execution engine — parses, optimizes, plans, and executes queries."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from common.interfaces import DatabaseEngine, EngineType, Query
from common.types import Value

from .ast import SelectNode
from .benchmark import BenchmarkCollector, BenchmarkEntry
from .cache import QueryCache
from .canonical import CanonicalColumn, CanonicalResult, CanonicalRow
from .errors import ExecutionError
from .logical_plan import LogicalPlanBuilder, logical_plan_to_text
from .optimizer import QueryOptimizer
from .parser import Parser
from .physical_plans import (
    KGPhysicalPlanBuilder,
    PhysicalPlan,
    SheafPhysicalPlanBuilder,
    physical_plan_to_text,
)
from .semantic import SemanticAnalyzer
from .statistics import StatisticsStore


@dataclass
class ExecutionPlan:
    logical_plan: LogicalPlan | None = None
    optimized_plan: LogicalPlan | None = None
    physical_plan: PhysicalPlan | None = None
    ast: SelectNode | None = None


@dataclass
class ExecutionResult:
    canonical: CanonicalResult
    execution_plan: ExecutionPlan
    optimizer_rules: list[str] = field(default_factory=list)


class QueryExecutionEngine:
    def __init__(
        self,
        kg_engine: DatabaseEngine | None = None,
        sheaf_engine: DatabaseEngine | None = None,
        default_engine: EngineType = EngineType.KNOWLEDGE_GRAPH,
    ) -> None:
        self._kg = kg_engine
        self._sheaf = sheaf_engine
        self._default = default_engine
        self._cache = QueryCache()
        self._stats = StatisticsStore()
        self._optimizer = QueryOptimizer()
        self._benchmark = BenchmarkCollector()

    def execute_query(
        self,
        query: Query | str,
        engine: EngineType | None = None,
        use_cache: bool = True,
    ) -> ExecutionResult:
        query_text = query.query if isinstance(query, Query) else query

        exec_plan = ExecutionPlan()

        parser = Parser(query_text)
        ast = parser.parse()
        exec_plan.ast = ast

        SemanticAnalyzer().analyze(ast)

        builder = LogicalPlanBuilder()
        logical = builder.build(ast)
        exec_plan.logical_plan = logical

        optimized = self._optimizer.optimize(logical)
        exec_plan.optimized_plan = optimized

        engine_type = engine or self._default
        physical = self._build_physical(engine_type, optimized)
        exec_plan.physical_plan = physical

        start = time.perf_counter()
        try:
            result = self._run_physical(engine_type, physical)
        except Exception as e:
            raise ExecutionError(str(e)) from e
        elapsed = (time.perf_counter() - start) * 1000

        canonical = CanonicalResult(
            columns=result.columns,
            rows=tuple(result.rows),
            row_count=len(result.rows),
            execution_time_ms=elapsed,
            engine_hint=engine_type.name,
        )

        entry = BenchmarkEntry(
            query_text=query_text,
            engine=engine_type.name,
            execution_time_ms=elapsed,
            row_count=len(result.rows),
            optimizer_rules=self._optimizer.applied_rules(),
            estimated_cost=physical.estimated_cost,
        )
        self._benchmark.record(entry)

        return ExecutionResult(
            canonical=canonical,
            execution_plan=exec_plan,
            optimizer_rules=self._optimizer.applied_rules(),
        )

    def explain(self, query: Query | str, engine: EngineType | None = None) -> str:
        query_text = query.query if isinstance(query, Query) else query

        parser = Parser(query_text)
        ast = parser.parse()

        SemanticAnalyzer().analyze(ast)

        builder = LogicalPlanBuilder()
        logical = builder.build(ast)

        optimized = self._optimizer.optimize(logical)

        engine_type = engine or self._default
        physical = self._build_physical(engine_type, optimized)

        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("EXPLAIN QUERY PLAN")
        lines.append("=" * 60)
        lines.append(f"\nQuery: {query_text}")
        lines.append("\n--- AST ---")
        lines.append(self._ast_to_text(ast))
        lines.append("\n--- Logical Plan ---")
        lines.append(logical_plan_to_text(logical))
        lines.append("\n--- Optimized Plan ---")
        lines.append(self._optimizer.explain(optimized))
        lines.append(f"\n--- Physical Plan ({engine_type.name}) ---")
        lines.append(physical_plan_to_text(physical))
        lines.append("=" * 60)
        return "\n".join(lines)

    def explain_analyze(self, query: Query | str) -> str:
        result = self.execute_query(query)
        lines: list[str] = []
        lines.append(self.explain(query))
        lines.append("\n--- Execution Results ---")
        lines.append(f"Engine: {result.canonical.engine_hint}")
        lines.append(f"Rows: {result.canonical.row_count}")
        lines.append(f"Time: {result.canonical.execution_time_ms:.2f}ms")
        lines.append(f"Optimizer Rules: {', '.join(result.optimizer_rules)}")
        if result.canonical.row_count <= 20:
            lines.append(f"\n{result.canonical.to_pretty_string()}")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _build_physical(self, engine: EngineType, logical: LogicalPlan) -> PhysicalPlan:
        if engine == EngineType.SHEAF_DATABASE:
            return SheafPhysicalPlanBuilder().build(logical)
        return KGPhysicalPlanBuilder().build(logical)

    def _run_physical(
        self,
        engine: EngineType,
        plan: PhysicalPlan,
    ) -> CanonicalResult:
        actual = self._kg if engine == EngineType.KNOWLEDGE_GRAPH else self._sheaf
        if actual is None:
            return CanonicalResult(
                columns=(CanonicalColumn(name="result", data_type="string"),),
                rows=(
                    CanonicalRow(values=(Value(inner=f"({engine.name} engine not available)"),)),
                ),
            )
        query = Query(text=plan.root.detail)
        qr = actual.execute(query)
        cols = tuple(CanonicalColumn(name=c.name, data_type=c.data_type) for c in qr.columns)
        rows = tuple(
            CanonicalRow(values=tuple(canonical_value(v) for v in r.values)) for r in qr.rows
        )
        return CanonicalResult(columns=cols, rows=rows)

    def benchmark(self, query: Query | str, engine: EngineType | None = None) -> str:
        result = self.execute_query(query, engine=engine)
        self._benchmark.summary()
        lines: list[str] = []
        lines.append("Benchmark Results:")
        lines.append(f"  Engine: {result.canonical.engine_hint}")
        lines.append(f"  Time: {result.canonical.execution_time_ms:.2f}ms")
        lines.append(f"  Rows: {result.canonical.row_count}")
        lines.append(f"  Estimated Cost: {result.execution_plan.physical_plan.estimated_cost:.1f}")
        lines.append(f"  Optimizer Rules: {', '.join(result.optimizer_rules)}")
        lines.append(f"  Cache Hit Rate: {self._cache.parsed.hit_rate():.1%}")
        return "\n".join(lines)

    @property
    def cache(self) -> QueryCache:
        return self._cache

    @property
    def stats(self) -> StatisticsStore:
        return self._stats

    @property
    def benchmark_collector(self) -> BenchmarkCollector:
        return self._benchmark

    def _ast_to_text(self, node: SelectNode, indent: int = 0) -> str:
        prefix = "  " * indent
        lines = [f"{prefix}SELECT"]
        if node.distinct:
            lines.append(f"{prefix}  DISTINCT")
        if node.columns:
            lines.append(f"{prefix}  columns: {[str(c) for c in node.columns]}")
        if node.source:
            lines.append(
                f"{prefix}  FROM {node.source.value if hasattr(node.source, 'value') else node.source}"
            )
        if node.filters:
            conds = [str(f) for f in node.filters]
            lines.append(f"{prefix}  WHERE {' '.join(conds)}")
        if node.aggregates:
            lines.append(f"{prefix}  GROUP BY {[str(a) for a in node.aggregates]}")
        if node.order:
            lines.append(f"{prefix}  ORDER BY {[str(o) for o in node.order]}")
        if node.limit is not None:
            limit = node.limit
            cnt = limit.count if hasattr(limit, "count") else str(limit)
            lines.append(f"{prefix}  LIMIT {cnt}")
        return "\n".join(lines)


def canonical_value(v: Value) -> Value:
    if isinstance(v.inner, (list, tuple, dict)):
        return Value(inner=str(v.inner))
    return v
