"""Physical plan generation for KG and Sheaf engines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from common.interfaces import EngineType

from .logical_plan import (
    AggregateNode as LogicalAggregate,
)
from .logical_plan import (
    ContextFilterNode,
    FilterNode,
    LogicalNode,
    LogicalPlan,
    NeighborhoodFilterNode,
    ProvenanceFilterNode,
    ScanNode,
    SelectionNode,
    SortNode,
    TemporalFilterNode,
)
from .logical_plan import (
    JoinNode as LogicalJoin,
)
from .logical_plan import (
    LimitNode as LogicalLimit,
)
from .logical_plan import (
    ProjectionNode as LogicalProjection,
)
from .logical_plan import (
    UnionNode as LogicalUnion,
)


class PhysicalOperatorType(Enum):
    KG_INDEX_SEEK = auto()
    KG_TRIPLE_SCAN = auto()
    KG_HASH_JOIN = auto()
    KG_NESTED_LOOP_JOIN = auto()
    KG_FILTER = auto()
    KG_AGGREGATE = auto()
    KG_SORT = auto()
    KG_LIMIT = auto()
    KG_PROJECTION = auto()
    KG_UNION = auto()

    SHEAF_OPEN_SET_LOOKUP = auto()
    SHEAF_LOCAL_SECTION_LOOKUP = auto()
    SHEAF_RESTRICTION_TRAVERSAL = auto()
    SHEAF_NEIGHBORHOOD_LOOKUP = auto()
    SHEAF_GLOBAL_SECTION_CONSTRUCTION = auto()
    SHEAF_CONSISTENCY_VERIFICATION = auto()
    SHEAF_FILTER = auto()
    SHEAF_AGGREGATE = auto()
    SHEAF_SORT = auto()
    SHEAF_LIMIT = auto()
    SHEAF_PROJECTION = auto()
    SHEAF_UNION = auto()


PHYSICAL_COST_ESTIMATES: dict[PhysicalOperatorType, float] = {
    PhysicalOperatorType.KG_INDEX_SEEK: 1.0,
    PhysicalOperatorType.KG_TRIPLE_SCAN: 10.0,
    PhysicalOperatorType.KG_HASH_JOIN: 15.0,
    PhysicalOperatorType.KG_NESTED_LOOP_JOIN: 20.0,
    PhysicalOperatorType.KG_FILTER: 2.0,
    PhysicalOperatorType.KG_AGGREGATE: 5.0,
    PhysicalOperatorType.KG_SORT: 8.0,
    PhysicalOperatorType.KG_LIMIT: 1.0,
    PhysicalOperatorType.KG_PROJECTION: 1.0,
    PhysicalOperatorType.KG_UNION: 3.0,
    PhysicalOperatorType.SHEAF_OPEN_SET_LOOKUP: 1.0,
    PhysicalOperatorType.SHEAF_LOCAL_SECTION_LOOKUP: 2.0,
    PhysicalOperatorType.SHEAF_RESTRICTION_TRAVERSAL: 5.0,
    PhysicalOperatorType.SHEAF_NEIGHBORHOOD_LOOKUP: 2.0,
    PhysicalOperatorType.SHEAF_GLOBAL_SECTION_CONSTRUCTION: 50.0,
    PhysicalOperatorType.SHEAF_CONSISTENCY_VERIFICATION: 10.0,
    PhysicalOperatorType.SHEAF_FILTER: 2.0,
    PhysicalOperatorType.SHEAF_AGGREGATE: 5.0,
    PhysicalOperatorType.SHEAF_SORT: 8.0,
    PhysicalOperatorType.SHEAF_LIMIT: 1.0,
    PhysicalOperatorType.SHEAF_PROJECTION: 1.0,
    PhysicalOperatorType.SHEAF_UNION: 3.0,
}


@dataclass(frozen=True)
class PhysicalPlanNode:
    operator: PhysicalOperatorType
    detail: str = ""
    children: tuple[PhysicalPlanNode, ...] = ()
    estimated_cost: float = 0.0
    source_node: LogicalNode | None = None

    def __repr__(self) -> str:
        return f"{self.operator.name}({self.detail}, cost={self.estimated_cost:.1f})"


@dataclass(frozen=True)
class PhysicalPlan:
    root: PhysicalPlanNode
    engine_type: EngineType
    estimated_cost: float = 0.0

    def __repr__(self) -> str:
        return f"PhysicalPlan({self.engine_type.name}, cost={self.estimated_cost:.1f})"


def physical_plan_to_text(plan: PhysicalPlan) -> str:
    lines: list[str] = []

    def walk(node: PhysicalPlanNode, depth: int) -> None:
        prefix = "  " * depth
        lines.append(f"{prefix}{node.operator.name}({node.detail})")
        for child in node.children:
            walk(child, depth + 1)

    lines.append(f"Engine: {plan.engine_type.name}")
    lines.append(f"Estimated Cost: {plan.estimated_cost:.1f}")
    walk(plan.root, 0)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Physical plan builders
# ---------------------------------------------------------------------------


class KGPhysicalPlanBuilder:
    def build(self, logical_plan: LogicalPlan) -> PhysicalPlan:
        root = self._translate(logical_plan.root)
        cost = self._total_cost(root)
        return PhysicalPlan(root=root, engine_type=EngineType.KNOWLEDGE_GRAPH, estimated_cost=cost)

    def _translate(self, node: LogicalNode) -> PhysicalPlanNode:
        match node:
            case ScanNode() as s:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_INDEX_SEEK,
                    detail=f"subject={s.source}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_INDEX_SEEK],
                    source_node=s,
                )
            case SelectionNode() as s:
                child = self._translate(s.children[0]) if s.children else self._empty_scan()
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_FILTER,
                    detail=s.condition,
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_FILTER],
                    source_node=s,
                )
            case LogicalProjection() as p:
                children = tuple(self._translate(c) for c in p.children) if p.children else ()
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_PROJECTION,
                    detail=f"cols={','.join(p.expressions)}, distinct={p.distinct}",
                    children=children,
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_PROJECTION],
                    source_node=p,
                )
            case LogicalJoin() as j:
                children = tuple(self._translate(c) for c in j.children) if j.children else ()
                op = (
                    PhysicalOperatorType.KG_HASH_JOIN
                    if j.join_type == "inner"
                    else PhysicalOperatorType.KG_NESTED_LOOP_JOIN
                )
                return PhysicalPlanNode(
                    operator=op,
                    detail=f"on={j.condition}",
                    children=children,
                    estimated_cost=PHYSICAL_COST_ESTIMATES[op],
                    source_node=j,
                )
            case LogicalAggregate() as a:
                child = self._translate(a.children[0]) if a.children else self._empty_scan()
                gb = ",".join(a.group_by)
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_AGGREGATE,
                    detail=f"{a.function}({a.aggregate_column}) group_by=({gb})",
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_AGGREGATE],
                    source_node=a,
                )
            case SortNode() as s:
                child = self._translate(s.children[0]) if s.children else self._empty_scan()
                cols = ",".join(f"{c} {d}" for c, d in s.sort_columns)
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_SORT,
                    detail=cols,
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_SORT],
                    source_node=s,
                )
            case LogicalLimit() as l:
                child = self._translate(l.children[0]) if l.children else self._empty_scan()
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_LIMIT,
                    detail=f"limit={l.limit}, offset={l.offset}",
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_LIMIT],
                    source_node=l,
                )
            case LogicalUnion():
                children = tuple(self._translate(c) for c in node.children)
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_UNION,
                    children=children,
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_UNION],
                    source_node=node,
                )
            case FilterNode() as f:
                child = self._translate(f.children[0]) if f.children else self._empty_scan()
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_FILTER,
                    detail=f.condition,
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_FILTER],
                    source_node=f,
                )
            case TemporalFilterNode() as t:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_FILTER,
                    detail=f"temporal={t.start}..{t.end}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_FILTER],
                    source_node=t,
                )
            case ContextFilterNode() as c:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_FILTER,
                    detail=f"context={c.context}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_FILTER],
                    source_node=c,
                )
            case ProvenanceFilterNode() as p:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_FILTER,
                    detail=f"provenance={p.source}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_FILTER],
                    source_node=p,
                )
            case NeighborhoodFilterNode() as n:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.KG_FILTER,
                    detail=f"neighborhood={n.entity}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_FILTER],
                    source_node=n,
                )
            case _:
                return self._empty_scan()

    def _empty_scan(self) -> PhysicalPlanNode:
        return PhysicalPlanNode(
            operator=PhysicalOperatorType.KG_TRIPLE_SCAN,
            detail="*",
            estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.KG_TRIPLE_SCAN],
        )

    def _total_cost(self, node: PhysicalPlanNode) -> float:
        c = node.estimated_cost
        for child in node.children:
            c += self._total_cost(child)
        return c


class SheafPhysicalPlanBuilder:
    def build(self, logical_plan: LogicalPlan) -> PhysicalPlan:
        root = self._translate(logical_plan.root)
        cost = self._total_cost(root)
        return PhysicalPlan(root=root, engine_type=EngineType.SHEAF_DATABASE, estimated_cost=cost)

    def _translate(self, node: LogicalNode) -> PhysicalPlanNode:
        match node:
            case ScanNode() as s:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_OPEN_SET_LOOKUP,
                    detail=f"entity={s.source}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[
                        PhysicalOperatorType.SHEAF_OPEN_SET_LOOKUP
                    ],
                    source_node=s,
                )
            case SelectionNode() as s:
                child = (
                    self._translate(s.children[0]) if s.children else self._local_section_lookup()
                )
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_FILTER,
                    detail=s.condition,
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.SHEAF_FILTER],
                    source_node=s,
                )
            case LogicalProjection() as p:
                children = tuple(self._translate(c) for c in p.children) if p.children else ()
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_PROJECTION,
                    detail=f"cols={','.join(p.expressions)}, distinct={p.distinct}",
                    children=children,
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.SHEAF_PROJECTION],
                    source_node=p,
                )
            case LogicalJoin() as j:
                children = tuple(self._translate(c) for c in j.children) if j.children else ()
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_RESTRICTION_TRAVERSAL,
                    detail=f"on={j.condition}",
                    children=children,
                    estimated_cost=PHYSICAL_COST_ESTIMATES[
                        PhysicalOperatorType.SHEAF_RESTRICTION_TRAVERSAL
                    ],
                    source_node=j,
                )
            case LogicalAggregate() as a:
                child = (
                    self._translate(a.children[0]) if a.children else self._local_section_lookup()
                )
                gb = ",".join(a.group_by)
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_AGGREGATE,
                    detail=f"{a.function}({a.aggregate_column}) group_by=({gb})",
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.SHEAF_AGGREGATE],
                    source_node=a,
                )
            case SortNode() as s:
                child = (
                    self._translate(s.children[0]) if s.children else self._local_section_lookup()
                )
                cols = ",".join(f"{c} {d}" for c, d in s.sort_columns)
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_SORT,
                    detail=cols,
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.SHEAF_SORT],
                    source_node=s,
                )
            case LogicalLimit() as l:
                child = (
                    self._translate(l.children[0]) if l.children else self._local_section_lookup()
                )
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_LIMIT,
                    detail=f"limit={l.limit}, offset={l.offset}",
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.SHEAF_LIMIT],
                    source_node=l,
                )
            case LogicalUnion():
                children = tuple(self._translate(c) for c in node.children)
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_UNION,
                    children=children,
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.SHEAF_UNION],
                    source_node=node,
                )
            case FilterNode() as f:
                child = (
                    self._translate(f.children[0]) if f.children else self._local_section_lookup()
                )
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_FILTER,
                    detail=f.condition,
                    children=(child,),
                    estimated_cost=PHYSICAL_COST_ESTIMATES[PhysicalOperatorType.SHEAF_FILTER],
                    source_node=f,
                )
            case TemporalFilterNode() as t:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_LOCAL_SECTION_LOOKUP,
                    detail=f"temporal={t.start}..{t.end}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[
                        PhysicalOperatorType.SHEAF_LOCAL_SECTION_LOOKUP
                    ],
                    source_node=t,
                )
            case ContextFilterNode() as c:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_LOCAL_SECTION_LOOKUP,
                    detail=f"context={c.context}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[
                        PhysicalOperatorType.SHEAF_LOCAL_SECTION_LOOKUP
                    ],
                    source_node=c,
                )
            case ProvenanceFilterNode() as p:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_NEIGHBORHOOD_LOOKUP,
                    detail=f"provenance={p.source}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[
                        PhysicalOperatorType.SHEAF_NEIGHBORHOOD_LOOKUP
                    ],
                    source_node=p,
                )
            case NeighborhoodFilterNode() as n:
                return PhysicalPlanNode(
                    operator=PhysicalOperatorType.SHEAF_NEIGHBORHOOD_LOOKUP,
                    detail=f"neighborhood={n.entity}",
                    estimated_cost=PHYSICAL_COST_ESTIMATES[
                        PhysicalOperatorType.SHEAF_NEIGHBORHOOD_LOOKUP
                    ],
                    source_node=n,
                )
            case _:
                return self._global_section_construction()

    def _local_section_lookup(self) -> PhysicalPlanNode:
        return PhysicalPlanNode(
            operator=PhysicalOperatorType.SHEAF_LOCAL_SECTION_LOOKUP,
            detail="*",
            estimated_cost=PHYSICAL_COST_ESTIMATES[
                PhysicalOperatorType.SHEAF_LOCAL_SECTION_LOOKUP
            ],
        )

    def _global_section_construction(self) -> PhysicalPlanNode:
        return PhysicalPlanNode(
            operator=PhysicalOperatorType.SHEAF_GLOBAL_SECTION_CONSTRUCTION,
            detail="*",
            estimated_cost=PHYSICAL_COST_ESTIMATES[
                PhysicalOperatorType.SHEAF_GLOBAL_SECTION_CONSTRUCTION
            ],
        )

    def _total_cost(self, node: PhysicalPlanNode) -> float:
        c = node.estimated_cost
        for child in node.children:
            c += self._total_cost(child)
        return c
