"""Logical and physical plan operators for Knowledge Graph query execution.

Implements:
  - Logical operators: Scan, IndexSeek, Filter, Join, Project, Aggregate, Sort, Limit
  - Physical plan builder that translates logical operators into executable form
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from common.safe_eval import safe_eval

# ---------------------------------------------------------------------------
# Join algorithms
# ---------------------------------------------------------------------------


class JoinAlgorithm(Enum):
    NESTED_LOOP = auto()
    HASH_JOIN = auto()


# ---------------------------------------------------------------------------
# Logical plan operators
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LogicalScan:
    """Full scan of the triple table."""

    alias: str = "t"
    filter_expr: str | None = None


@dataclass(frozen=True)
class LogicalIndexSeek:
    """Index seek on SPO/POS/OPS."""

    index: str  # "SPO", "POS", "OPS"
    subject: int | None = None
    predicate: int | None = None
    obj: int | None = None
    alias: str = "t"


@dataclass(frozen=True)
class LogicalFilter:
    """Filter rows by a predicate."""

    condition: str
    child: LogicalNode


@dataclass(frozen=True)
class LogicalJoin:
    """Join two sub-plans."""

    left: LogicalNode
    right: LogicalNode
    condition: str | None = None
    algorithm: JoinAlgorithm = JoinAlgorithm.NESTED_LOOP


@dataclass(frozen=True)
class LogicalProject:
    """Project a subset of columns."""

    columns: tuple[str, ...]
    child: LogicalNode


@dataclass(frozen=True)
class LogicalAggregate:
    """Group and aggregate."""

    group_by: tuple[str, ...]
    aggregates: tuple[tuple[str, str], ...]  # (function, column)
    child: LogicalNode


@dataclass(frozen=True)
class LogicalSort:
    """Sort by a column."""

    column: str
    child: LogicalNode
    ascending: bool = True


@dataclass(frozen=True)
class LogicalLimit:
    """Limit the number of rows."""

    limit: int
    child: LogicalNode
    offset: int = 0


LogicalNode = (
    LogicalScan
    | LogicalIndexSeek
    | LogicalFilter
    | LogicalJoin
    | LogicalProject
    | LogicalAggregate
    | LogicalSort
    | LogicalLimit
)


# ---------------------------------------------------------------------------
# Physical plan operators
# ---------------------------------------------------------------------------


@dataclass
class PhysicalScan:
    alias: str = "t"


@dataclass
class PhysicalIndexSeek:
    index: str
    params: dict[str, int | None] = field(default_factory=dict)
    alias: str = "t"


@dataclass
class PhysicalFilter:
    condition: str
    child: PhysicalNode


@dataclass
class PhysicalNestedLoopJoin:
    left: PhysicalNode
    right: PhysicalNode
    condition: str | None = None


@dataclass
class PhysicalHashJoin:
    left: PhysicalNode
    right: PhysicalNode
    build_side_column: str
    probe_side_column: str


@dataclass
class PhysicalProject:
    columns: tuple[str, ...]
    child: PhysicalNode


@dataclass
class PhysicalAggregate:
    group_by: tuple[str, ...]
    aggregates: tuple[tuple[str, str], ...]
    child: PhysicalNode


@dataclass
class PhysicalSort:
    column: str
    ascending: bool
    child: PhysicalNode


@dataclass
class PhysicalLimit:
    limit: int
    offset: int
    child: PhysicalNode


PhysicalNode = (
    PhysicalScan
    | PhysicalIndexSeek
    | PhysicalFilter
    | PhysicalNestedLoopJoin
    | PhysicalHashJoin
    | PhysicalProject
    | PhysicalAggregate
    | PhysicalSort
    | PhysicalLimit
)


# ---------------------------------------------------------------------------
# Physical plan builder
# ---------------------------------------------------------------------------


class PhysicalPlanBuilder:
    """Converts a logical plan into a physical plan with concrete algorithms."""

    def build(self, logical: LogicalNode) -> PhysicalNode:
        if isinstance(logical, LogicalScan):
            return PhysicalScan(alias=logical.alias)
        if isinstance(logical, LogicalIndexSeek):
            return PhysicalIndexSeek(
                index=logical.index,
                params={"s": logical.subject, "p": logical.predicate, "o": logical.obj},
                alias=logical.alias,
            )
        if isinstance(logical, LogicalFilter):
            return PhysicalFilter(
                condition=logical.condition,
                child=self.build(logical.child),
            )
        if isinstance(logical, LogicalJoin):
            if logical.algorithm == JoinAlgorithm.HASH_JOIN:
                left_col = "subject_id"
                right_col = "object_id"
                if logical.condition:
                    parts = logical.condition.split("=")
                    if len(parts) == 2:
                        left_col = parts[0].strip()
                        right_col = parts[1].strip()
                return PhysicalHashJoin(
                    left=self.build(logical.left),
                    right=self.build(logical.right),
                    build_side_column=left_col,
                    probe_side_column=right_col,
                )
            return PhysicalNestedLoopJoin(
                left=self.build(logical.left),
                right=self.build(logical.right),
                condition=logical.condition,
            )
        if isinstance(logical, LogicalProject):
            return PhysicalProject(
                columns=logical.columns,
                child=self.build(logical.child),
            )
        if isinstance(logical, LogicalAggregate):
            return PhysicalAggregate(
                group_by=logical.group_by,
                aggregates=logical.aggregates,
                child=self.build(logical.child),
            )
        if isinstance(logical, LogicalSort):
            return PhysicalSort(
                column=logical.column,
                ascending=logical.ascending,
                child=self.build(logical.child),
            )
        if isinstance(logical, LogicalLimit):
            return PhysicalLimit(
                limit=logical.limit,
                offset=logical.offset,
                child=self.build(logical.child),
            )
        raise ValueError(f"Unknown logical node: {type(logical)}")


# ---------------------------------------------------------------------------
# Plan executor (interpreted)
# ---------------------------------------------------------------------------


class PlanExecutor:
    """Executes a physical plan against a data source."""

    def __init__(self, index_lookup: Callable[..., list[tuple]]) -> None:
        self._index_lookup = index_lookup

    def execute(self, plan: PhysicalNode) -> list[dict[str, Any]]:
        return self._eval(plan)

    def _eval(self, node: PhysicalNode) -> list[dict[str, Any]]:
        if isinstance(node, PhysicalScan):
            rows = self._index_lookup(None, None, None)
            return [
                {
                    "t.subject_id": r[0],
                    "t.predicate_id": r[1],
                    "t.object_id": r[2],
                    "t.object_type": r[3],
                    "t.event_id": r[4],
                    "t.role": r[5],
                }
                for r in rows
            ]

        if isinstance(node, PhysicalIndexSeek):
            params = node.params
            rows = self._index_lookup(params.get("s"), params.get("p"), params.get("o"))
            alias = node.alias
            return [
                {
                    f"{alias}.subject_id": r[0],
                    f"{alias}.predicate_id": r[1],
                    f"{alias}.object_id": r[2],
                    f"{alias}.object_type": r[3],
                    f"{alias}.event_id": r[4],
                    f"{alias}.role": r[5],
                }
                for r in rows
            ]

        if isinstance(node, PhysicalFilter):
            rows = self._eval(node.child)
            return [r for r in rows if self._eval_condition(node.condition, r)]

        if isinstance(node, PhysicalNestedLoopJoin):
            left = self._eval(node.left)
            right = self._eval(node.right)
            results: list[dict[str, Any]] = []
            for lr in left:
                for rr in right:
                    if node.condition is None or self._eval_condition(
                        node.condition, {**lr, **rr}
                    ):
                        results.append({**lr, **rr})
            return results

        if isinstance(node, PhysicalHashJoin):
            left = self._eval(node.left)
            right = self._eval(node.right)
            build: dict[str, list[dict]] = {}
            for row in left:
                key = str(row.get(node.build_side_column, ""))
                build.setdefault(key, []).append(row)
            results = []
            for row in right:
                key = str(row.get(node.probe_side_column, ""))
                for match in build.get(key, []):
                    results.append({**match, **row})
            return results

        if isinstance(node, PhysicalProject):
            rows = self._eval(node.child)
            return [{k: r[k] for k in node.columns if k in r} for r in rows]

        if isinstance(node, PhysicalSort):
            rows = self._eval(node.child)
            return sorted(rows, key=lambda r: r.get(node.column, ""), reverse=not node.ascending)

        if isinstance(node, PhysicalLimit):
            rows = self._eval(node.child)
            return rows[node.offset : node.offset + node.limit]

        if isinstance(node, PhysicalAggregate):
            rows = self._eval(node.child)
            groups: dict[str, list[dict]] = {}
            for r in rows:
                key = "|".join(str(r.get(c, "")) for c in node.group_by)
                groups.setdefault(key, []).append(r)
            results = []
            for key, grp in groups.items():
                row: dict[str, Any] = {}
                parts = key.split("|")
                for i, c in enumerate(node.group_by):
                    row[c] = parts[i] if i < len(parts) else ""
                for func, col in node.aggregates:
                    vals = [r.get(col, 0) for r in grp]
                    try:
                        numeric_vals = [float(v) for v in vals]
                    except (ValueError, TypeError):
                        numeric_vals = []
                    if func == "COUNT":
                        row[f"COUNT({col})"] = len(vals)
                    elif func == "SUM":
                        row[f"SUM({col})"] = sum(numeric_vals)
                    elif func == "AVG":
                        row[f"AVG({col})"] = (
                            sum(numeric_vals) / len(numeric_vals) if numeric_vals else 0
                        )
                    elif func == "MIN":
                        row[f"MIN({col})"] = min(vals) if vals else ""
                    elif func == "MAX":
                        row[f"MAX({col})"] = max(vals) if vals else ""
                results.append(row)
            return results

        raise ValueError(f"Unknown physical node: {type(node)}")

    def _eval_condition(self, condition: str, row: dict[str, Any]) -> bool:
        try:
            return bool(safe_eval(condition, dict(row)))
        except Exception:
            return True
