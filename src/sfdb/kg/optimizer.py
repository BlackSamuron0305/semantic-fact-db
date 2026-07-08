"""Query optimizer for the Knowledge Graph engine.

Implements cost-based optimization:
  - Cost estimation for scan, index seek, join, filter
  - Join reordering based on estimated cardinality
  - Filter pushdown (move filters closer to data sources)
  - Index selection (choose SPO/POS/OPS based on predicate binding)
  - Explain plan generation
"""

from __future__ import annotations

from dataclasses import dataclass

from .planner import (
    JoinAlgorithm,
    LogicalFilter,
    LogicalIndexSeek,
    LogicalJoin,
    LogicalLimit,
    LogicalNode,
    LogicalProject,
    LogicalScan,
    LogicalSort,
)


@dataclass
class TableStatistics:
    total_triples: int = 0
    distinct_subjects: int = 0
    distinct_predicates: int = 0
    distinct_objects: int = 0


@dataclass
class CostModel:
    seq_page_cost: float = 1.0
    random_page_cost: float = 4.0
    cpu_tuple_cost: float = 0.01
    cpu_operator_cost: float = 0.0025


class QueryOptimizer:
    """Cost-based query optimizer for the Knowledge Graph.

    Applies transformations to a logical plan to minimise estimated cost.
    """

    def __init__(self, stats: TableStatistics | None = None) -> None:
        self._stats = stats or TableStatistics()
        self._cost_model = CostModel()

    def optimize(self, plan: LogicalNode) -> LogicalNode:
        plan = self._push_filters_down(plan)
        plan = self._reorder_joins(plan)
        plan = self._select_indexes(plan)
        return plan

    def estimate_cost(self, plan: LogicalNode) -> float:
        if isinstance(plan, LogicalScan):
            return self._cost_scan()
        if isinstance(plan, LogicalIndexSeek):
            return self._cost_index_seek(plan)
        if isinstance(plan, LogicalFilter):
            child_cost = self.estimate_cost(plan.child)
            return child_cost + self._cost_filter(plan.child)
        if isinstance(plan, LogicalJoin):
            left_cost = self.estimate_cost(plan.left)
            right_cost = self.estimate_cost(plan.right)
            return left_cost + right_cost + self._cost_join(plan)
        if isinstance(plan, LogicalProject):
            return self.estimate_cost(plan.child) + 0.01
        if isinstance(plan, LogicalSort):
            return self.estimate_cost(plan.child) + self._cost_sort(plan)
        if isinstance(plan, LogicalLimit):
            return self.estimate_cost(plan.child) + 0.01
        return 1.0

    def get_estimated_rows(self, plan: LogicalNode) -> int:
        if isinstance(plan, LogicalScan):
            return self._stats.total_triples
        if isinstance(plan, LogicalIndexSeek):
            return self._estimate_index_selectivity(plan)
        if isinstance(plan, LogicalFilter):
            return int(self.get_estimated_rows(plan.child) * 0.5)
        if isinstance(plan, LogicalLimit):
            return min(plan.limit, self.get_estimated_rows(plan.child))
        if isinstance(plan, LogicalJoin):
            left = self.get_estimated_rows(plan.left)
            right = self.get_estimated_rows(plan.right)
            if self._stats.total_triples > 0:
                return max(1, int(left * right / self._stats.total_triples))
            return left * right
        if isinstance(plan, LogicalProject):
            return self.get_estimated_rows(plan.child)
        if isinstance(plan, LogicalSort):
            return self.get_estimated_rows(plan.child)
        return 1000

    def explain(self, plan: LogicalNode, indent: str = "") -> list[str]:
        lines: list[str] = []
        cost = self.estimate_cost(plan)
        rows = self.get_estimated_rows(plan)
        if isinstance(plan, LogicalScan):
            lines.append(f"{indent}SeqScan on triples  (cost={cost:.2f}, rows={rows})")
        elif isinstance(plan, LogicalIndexSeek):
            params = f"s={plan.subject}, p={plan.predicate}, o={plan.obj}"
            lines.append(
                f"{indent}IndexSeek using {plan.index} ({params})  (cost={cost:.2f}, rows={rows})"
            )
        elif isinstance(plan, LogicalFilter):
            lines.append(f"{indent}Filter: {plan.condition}  (cost={cost:.2f}, rows={rows})")
            lines.extend(self.explain(plan.child, indent + "  "))
        elif isinstance(plan, LogicalJoin):
            algo = plan.algorithm.name
            lines.append(f"{indent}{algo} Join  (cost={cost:.2f}, rows={rows})")
            lines.append(f"{indent}  -> Left:")
            lines.extend(self.explain(plan.left, indent + "    "))
            lines.append(f"{indent}  -> Right:")
            lines.extend(self.explain(plan.right, indent + "    "))
        elif isinstance(plan, LogicalSort):
            order = "ASC" if plan.ascending else "DESC"
            lines.append(f"{indent}Sort ({plan.column} {order})  (cost={cost:.2f}, rows={rows})")
            lines.extend(self.explain(plan.child, indent + "  "))
        elif isinstance(plan, LogicalLimit):
            lines.append(
                f"{indent}Limit ({plan.limit}, offset={plan.offset})  (cost={cost:.2f}, rows={rows})"
            )
            lines.extend(self.explain(plan.child, indent + "  "))
        elif isinstance(plan, LogicalProject):
            cols = ", ".join(plan.columns)
            lines.append(f"{indent}Project ({cols})  (cost={cost:.2f}, rows={rows})")
            lines.extend(self.explain(plan.child, indent + "  "))
        else:
            lines.append(f"{indent}Unknown plan node  (cost={cost:.2f}, rows={rows})")
        return lines

    # ------------------------------------------------------------------
    # Internal transformations
    # ------------------------------------------------------------------

    def _push_filters_down(self, plan: LogicalNode) -> LogicalNode:
        if isinstance(plan, LogicalFilter):
            child = self._push_filters_down(plan.child)
            if isinstance(child, LogicalFilter):
                combined = f"({plan.condition}) AND ({child.condition})"
                return LogicalFilter(condition=combined, child=child.child)
            return LogicalFilter(condition=plan.condition, child=child)
        if isinstance(plan, LogicalJoin):
            return LogicalJoin(
                left=self._push_filters_down(plan.left),
                right=self._push_filters_down(plan.right),
                condition=plan.condition,
                algorithm=plan.algorithm,
            )
        if isinstance(plan, LogicalProject):
            return LogicalProject(columns=plan.columns, child=self._push_filters_down(plan.child))
        if isinstance(plan, LogicalSort):
            return LogicalSort(
                column=plan.column,
                ascending=plan.ascending,
                child=self._push_filters_down(plan.child),
            )
        if isinstance(plan, LogicalLimit):
            return LogicalLimit(
                limit=plan.limit,
                offset=plan.offset,
                child=self._push_filters_down(plan.child),
            )
        return plan

    def _reorder_joins(self, plan: LogicalNode) -> LogicalNode:
        if isinstance(plan, LogicalJoin):
            left_cost = self.estimate_cost(plan.left)
            right_cost = self.estimate_cost(plan.right)
            if right_cost < left_cost:
                return LogicalJoin(
                    left=plan.right,
                    right=plan.left,
                    condition=plan.condition,
                    algorithm=JoinAlgorithm.HASH_JOIN,
                )
            left = self._reorder_joins(plan.left)
            right = self._reorder_joins(plan.right)
            return LogicalJoin(
                left=left,
                right=right,
                condition=plan.condition,
                algorithm=plan.algorithm,
            )
        if isinstance(plan, LogicalFilter):
            return LogicalFilter(condition=plan.condition, child=self._reorder_joins(plan.child))
        if isinstance(plan, LogicalProject):
            return LogicalProject(columns=plan.columns, child=self._reorder_joins(plan.child))
        return plan

    def _select_indexes(self, plan: LogicalNode) -> LogicalNode:
        if isinstance(plan, LogicalScan):
            return LogicalIndexSeek(index="SPO", subject=None, predicate=None, obj=None, alias="t")
        if isinstance(plan, LogicalFilter):
            return LogicalFilter(
                condition=plan.condition,
                child=self._select_indexes(plan.child),
            )
        if isinstance(plan, LogicalJoin):
            return LogicalJoin(
                left=self._select_indexes(plan.left),
                right=self._select_indexes(plan.right),
                condition=plan.condition,
                algorithm=plan.algorithm,
            )
        return plan

    # ------------------------------------------------------------------
    # Cost estimates
    # ------------------------------------------------------------------

    def _cost_scan(self) -> float:
        pages = max(1, self._stats.total_triples // 100)
        return (
            pages * self._cost_model.seq_page_cost
            + self._stats.total_triples * self._cost_model.cpu_tuple_cost
        )

    def _cost_index_seek(self, plan: LogicalIndexSeek) -> float:
        sel = self._estimate_index_selectivity(plan)
        return sel * self._cost_model.random_page_cost + sel * self._cost_model.cpu_tuple_cost

    def _cost_filter(self, child: LogicalNode) -> float:
        return self.get_estimated_rows(child) * self._cost_model.cpu_operator_cost

    def _cost_join(self, plan: LogicalJoin) -> float:
        left = self.get_estimated_rows(plan.left)
        right = self.get_estimated_rows(plan.right)
        if plan.algorithm == JoinAlgorithm.HASH_JOIN:
            return left + right + left * self._cost_model.cpu_operator_cost
        return left * right * self._cost_model.cpu_tuple_cost

    def _cost_sort(self, plan: LogicalSort) -> float:
        rows = self.get_estimated_rows(plan)
        return rows * math.log2(max(2, rows)) * self._cost_model.cpu_operator_cost

    def _estimate_index_selectivity(self, plan: LogicalIndexSeek) -> int:
        total = self._stats.total_triples
        if total == 0:
            return 0
        selectivity = 1.0
        if plan.subject is not None:
            selectivity *= 0.1
        if plan.predicate is not None:
            selectivity *= 0.1
        if plan.obj is not None:
            selectivity *= 0.1
        return max(1, int(total * selectivity))


import math
