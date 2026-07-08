"""Cost-based query optimizer with standard rewrite rules."""

from __future__ import annotations

from .logical_plan import (
    AggregateNode,
    ContextFilterNode,
    FilterNode,
    JoinNode,
    LimitNode,
    LogicalNode,
    LogicalOperatorType,
    LogicalPlan,
    NeighborhoodFilterNode,
    ProjectionNode,
    ProvenanceFilterNode,
    ScanNode,
    SelectionNode,
    SortNode,
    TemporalFilterNode,
    logical_plan_to_text,
)


class CostModel:
    def estimate_scan(self, source: str) -> float:
        return 10.0

    def estimate_selection(self, condition: str, input_card: float) -> float:
        return input_card * 0.5

    def estimate_projection(self, input_card: float) -> float:
        return input_card * 0.1

    def estimate_join(self, left_card: float, right_card: float) -> float:
        return left_card * right_card * 0.1

    def estimate_aggregate(self, input_card: float) -> float:
        return input_card * 0.3

    def estimate_sort(self, input_card: float) -> float:
        return input_card * input_card.log10() if input_card > 0 else 0

    def estimate_limit(self, input_card: float) -> float:
        return input_card * 0.05

    def estimate_filter(self, input_card: float, is_temporal: bool = False) -> float:
        return input_card * (0.3 if is_temporal else 0.5)


class OptimizerRule:
    name: str = "base"

    def apply(self, node: LogicalNode) -> LogicalNode:
        return node


class ConstantFolding(OptimizerRule):
    name = "constant_folding"

    def apply(self, node: LogicalNode) -> LogicalNode:
        if node.operator == LogicalOperatorType.SELECTION:
            cond = node.predicate
            if cond is True and node.children:
                return node.children[0]
            if cond is False:
                return ScanNode(LogicalOperatorType.SCAN, source="__empty__")
        return node


class PredicatePushdown(OptimizerRule):
    name = "predicate_pushdown"

    def apply(self, node: LogicalNode) -> LogicalNode:
        if node.operator == LogicalOperatorType.SELECTION and node.children:
            child = node.children[0]
            if child.operator in (
                LogicalOperatorType.JOIN,
                LogicalOperatorType.UNION,
            ):
                list(child.children)
                pushed = SelectionNode(
                    operator=LogicalOperatorType.SELECTION,
                    condition=node.predicate or "",
                    children=(),
                )
                updated = list(child.children)
                if updated:
                    new_node = type(child)(
                        operator=child.operator,
                        children=(pushed, *updated[1:]),
                        predicate=child.predicate,
                        columns=child.columns,
                        alias=child.alias,
                    )
                    return new_node
        return node


class ProjectionPushdown(OptimizerRule):
    name = "projection_pushdown"

    def apply(self, node: LogicalNode) -> LogicalNode:
        return node


class JoinReordering(OptimizerRule):
    name = "join_reordering"

    def apply(self, node: LogicalNode) -> LogicalNode:
        return node


class DeadOperatorRemoval(OptimizerRule):
    name = "dead_operator_removal"

    def apply(self, node: LogicalNode) -> LogicalNode:
        if node.operator == LogicalOperatorType.LIMIT and node.limit == 0:
            return ScanNode(LogicalOperatorType.SCAN, source="__empty__")
        return node


class LogicalSimplification(OptimizerRule):
    name = "logical_simplification"

    def apply(self, node: LogicalNode) -> LogicalNode:
        if node.operator == LogicalOperatorType.PROJECTION and not node.expressions:
            if node.children:
                return node.children[0]
        if node.operator == LogicalOperatorType.SELECTION and not node.predicate:
            if node.children:
                return node.children[0]
        return node


class QueryOptimizer:
    def __init__(self, cost_model: CostModel | None = None) -> None:
        self._cost_model = cost_model or CostModel()
        self._rules: list[OptimizerRule] = [
            ConstantFolding(),
            PredicatePushdown(),
            ProjectionPushdown(),
            JoinReordering(),
            DeadOperatorRemoval(),
            LogicalSimplification(),
        ]
        self._applied_rules: list[str] = []

    def optimize(self, plan: LogicalPlan, max_passes: int = 3) -> LogicalPlan:
        self._applied_rules = []
        current_root = plan.root

        for _ in range(max_passes):
            new_root = self._apply_rules(current_root)
            cost = self._estimate_node_cost(new_root)
            if new_root == current_root:
                break
            current_root = new_root

        nodes = self._collect_nodes(current_root)
        return LogicalPlan(root=current_root, estimated_cost=cost, nodes=tuple(nodes))

    def _apply_rules(self, node: LogicalNode) -> LogicalNode:
        result = node
        for rule in self._rules:
            new_result = rule.apply(result)
            if new_result != result:
                self._applied_rules.append(rule.name)
                result = new_result
        if node.children:
            new_children = tuple(self._apply_rules(c) for c in node.children)
            if new_children != node.children:
                result = type(node)(
                    operator=node.operator,
                    children=new_children,
                    predicate=node.predicate,
                    columns=node.columns,
                    alias=node.alias,
                )
        return result

    def _estimate_node_cost(self, node: LogicalNode) -> float:
        children_cost = sum(self._estimate_node_cost(c) for c in node.children)
        node_cost = self._node_cost(node)
        return children_cost + node_cost

    def _node_cost(self, node: LogicalNode) -> float:
        m = self._cost_model
        match node:
            case ScanNode() as s:
                return m.estimate_scan(s.source)
            case SelectionNode() as s:
                return m.estimate_selection(s.condition, 10)
            case ProjectionNode() as p:
                return m.estimate_projection(10)
            case JoinNode() as j:
                return m.estimate_join(10, 10)
            case AggregateNode() as a:
                return m.estimate_aggregate(10)
            case SortNode() as s:
                return m.estimate_sort(10)
            case LimitNode() as l:
                return m.estimate_limit(10)
            case FilterNode() as f:
                return m.estimate_filter(10)
            case TemporalFilterNode():
                return m.estimate_filter(10, is_temporal=True)
            case ContextFilterNode():
                return m.estimate_filter(10)
            case ProvenanceFilterNode():
                return m.estimate_filter(10)
            case NeighborhoodFilterNode():
                return m.estimate_filter(10)
            case _:
                return 1.0

    def _collect_nodes(self, node: LogicalNode) -> list[LogicalNode]:
        result = [node]
        for c in node.children:
            result.extend(self._collect_nodes(c))
        return result

    def applied_rules(self) -> list[str]:
        return list(self._applied_rules)

    def explain(self, plan: LogicalPlan) -> str:
        text = logical_plan_to_text(plan)
        rules = ", ".join(self._applied_rules) if self._applied_rules else "none"
        return f"Logical Plan:\n{text}\n\nOptimizer Rules Applied: {rules}\nEstimated Cost: {plan.estimated_cost:.1f}"
