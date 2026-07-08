"""Storage-independent logical plan operators."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class LogicalOperatorType(Enum):
    SCAN = auto()
    SELECTION = auto()
    PROJECTION = auto()
    JOIN = auto()
    AGGREGATE = auto()
    SORT = auto()
    LIMIT = auto()
    UNION = auto()
    FILTER = auto()
    TEMPORAL_FILTER = auto()
    CONTEXT_FILTER = auto()
    PROVENANCE_FILTER = auto()
    NEIGHBORHOOD_FILTER = auto()


@dataclass(frozen=True)
class LogicalPlan:
    root: LogicalNode
    estimated_cost: float = 0.0
    nodes: tuple[LogicalNode, ...] = ()

    def __repr__(self) -> str:
        return f"LogicalPlan(cost={self.estimated_cost:.1f}, root={self.root})"


@dataclass(frozen=True)
class LogicalNode:
    operator: LogicalOperatorType
    children: tuple[LogicalNode, ...] = ()
    predicate: Any = None
    columns: tuple[str, ...] = ()
    alias: str = ""


@dataclass(frozen=True)
class ScanNode(LogicalNode):
    source: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.SCAN)


@dataclass(frozen=True)
class SelectionNode(LogicalNode):
    condition: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.SELECTION)


@dataclass(frozen=True)
class ProjectionNode(LogicalNode):
    expressions: tuple[str, ...] = ()
    distinct: bool = False

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.PROJECTION)


@dataclass(frozen=True)
class JoinNode(LogicalNode):
    join_type: str = "inner"
    condition: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.JOIN)


@dataclass(frozen=True)
class AggregateNode(LogicalNode):
    function: str = "COUNT"
    group_by: tuple[str, ...] = ()
    aggregate_column: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.AGGREGATE)


@dataclass(frozen=True)
class SortNode(LogicalNode):
    sort_columns: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.SORT)


@dataclass(frozen=True)
class LimitNode(LogicalNode):
    limit: int = 0
    offset: int = 0

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.LIMIT)


@dataclass(frozen=True)
class UnionNode(LogicalNode):
    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.UNION)


@dataclass(frozen=True)
class FilterNode(LogicalNode):
    condition: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.FILTER)


@dataclass(frozen=True)
class TemporalFilterNode(LogicalNode):
    start: str = ""
    end: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.TEMPORAL_FILTER)


@dataclass(frozen=True)
class ContextFilterNode(LogicalNode):
    context: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.CONTEXT_FILTER)


@dataclass(frozen=True)
class ProvenanceFilterNode(LogicalNode):
    source: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.PROVENANCE_FILTER)


@dataclass(frozen=True)
class NeighborhoodFilterNode(LogicalNode):
    entity: str = ""

    def __post_init__(self):
        object.__setattr__(self, "operator", LogicalOperatorType.NEIGHBORHOOD_FILTER)


class LogicalPlanBuilder:
    def build(self, ast: Any) -> LogicalPlan:
        if hasattr(ast, "columns") and ast.columns:
            cols = tuple(str(c) for c in ast.columns)
        else:
            cols = ("*",)
        leaf = ScanNode(
            LogicalOperatorType.SCAN, source=str(ast.source) if ast.source else "default"
        )
        current: LogicalNode = leaf
        if hasattr(ast, "filters") and ast.filters:
            for f in ast.filters:
                current = SelectionNode(
                    LogicalOperatorType.SELECTION, condition=str(f), children=(current,)
                )
        if hasattr(ast, "order") and ast.order:
            sort_cols = []
            for o in ast.order:
                col = str(o.column) if hasattr(o, "column") else str(o)
                dir = "ASC"
                if hasattr(o, "direction"):
                    dir = o.direction.name if hasattr(o.direction, "name") else str(o.direction)
                sort_cols.append((col, dir))
            current = SortNode(
                LogicalOperatorType.SORT, sort_columns=tuple(sort_cols), children=(current,)
            )
        if hasattr(ast, "limit") and ast.limit:
            cnt = ast.limit.count if hasattr(ast.limit, "count") else 0
            off = ast.limit.offset if hasattr(ast.limit, "offset") else 0
            current = LimitNode(
                LogicalOperatorType.LIMIT, limit=cnt, offset=off, children=(current,)
            )
        if hasattr(ast, "distinct") and ast.distinct:
            current = ProjectionNode(
                LogicalOperatorType.PROJECTION,
                expressions=cols,
                distinct=True,
                children=(current,),
            )
        nodes = self._collect(current)
        cost = float(len(nodes))
        return LogicalPlan(root=current, estimated_cost=cost, nodes=tuple(nodes))

    def _collect(self, node: LogicalNode) -> list[LogicalNode]:
        result = [node]
        for child in node.children:
            result.extend(self._collect(child))
        return result


def logical_plan_to_text(plan: LogicalPlan) -> str:
    lines: list[str] = []

    def walk(node: LogicalNode, depth: int) -> None:
        prefix = "  " * depth
        op = node.operator.name
        match node:
            case ScanNode() as s:
                lines.append(f"{prefix}Scan({s.source})")
            case SelectionNode() as s:
                lines.append(f"{prefix}Selection({s.condition})")
            case ProjectionNode() as p:
                cols = ", ".join(p.expressions)
                d = " DISTINCT" if p.distinct else ""
                lines.append(f"{prefix}Projection({cols}){d}")
            case JoinNode() as j:
                lines.append(f"{prefix}Join({j.join_type}, {j.condition})")
            case AggregateNode() as a:
                gb = ", ".join(a.group_by) if a.group_by else "none"
                lines.append(
                    f"{prefix}Aggregate({a.function}({a.aggregate_column}) GROUP BY {gb})"
                )
            case SortNode() as s:
                cols = ", ".join(f"{c} {d}" for c, d in s.sort_columns)
                lines.append(f"{prefix}Sort({cols})")
            case LimitNode() as l:
                lines.append(f"{prefix}Limit({l.limit}, offset={l.offset})")
            case UnionNode():
                lines.append(f"{prefix}Union")
            case FilterNode() as f:
                lines.append(f"{prefix}Filter({f.condition})")
            case TemporalFilterNode() as t:
                lines.append(f"{prefix}TemporalFilter({t.start}..{t.end})")
            case ContextFilterNode() as c:
                lines.append(f"{prefix}ContextFilter({c.context})")
            case ProvenanceFilterNode() as p:
                lines.append(f"{prefix}ProvenanceFilter({p.source})")
            case NeighborhoodFilterNode() as n:
                lines.append(f"{prefix}NeighborhoodFilter({n.entity})")
            case _:
                lines.append(f"{prefix}{op}")
        for child in node.children:
            walk(child, depth + 1)

    walk(plan.root, 0)
    return "\n".join(lines)
