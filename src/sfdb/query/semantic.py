"""Semantic analysis for the query AST."""

from __future__ import annotations

from .ast import (
    AggregateNode,
    ASTNode,
    BinaryOpNode,
    ComparisonNode,
    ContextPredNode,
    FilterNode,
    FunctionCallNode,
    JoinNode,
    LimitNode,
    NeighborhoodPredNode,
    NodeType,
    OptionalNode,
    OrderNode,
    ProjectionNode,
    ProvenancePredNode,
    SelectNode,
    TemporalPredNode,
    UnaryOpNode,
    UnionNode,
)
from .errors import SemanticError


class SemanticAnalyzer:
    def __init__(self) -> None:
        self._errors: list[SemanticError] = []

    def analyze(self, node: ASTNode) -> list[SemanticError]:
        self._errors = []
        self._visit(node)
        return self._errors

    def _visit(self, node: ASTNode) -> None:
        visitor = {
            NodeType.SELECT: self._visit_select,
            NodeType.FILTER: self._visit_filter,
            NodeType.JOIN: self._visit_join,
            NodeType.PROJECTION: self._visit_projection,
            NodeType.AGGREGATE: self._visit_aggregate,
            NodeType.ORDER: self._visit_order,
            NodeType.LIMIT: self._visit_limit,
            NodeType.UNION: self._visit_union,
            NodeType.OPTIONAL: self._visit_optional,
            NodeType.BINARY_OP: self._visit_binary_op,
            NodeType.UNARY_OP: self._visit_unary_op,
            NodeType.COMPARISON: self._visit_comparison,
            NodeType.TEMPORAL_PRED: self._visit_temporal,
            NodeType.CONTEXT_PRED: self._visit_context,
            NodeType.PROVENANCE_PRED: self._visit_provenance,
            NodeType.NEIGHBORHOOD_PRED: self._visit_neighborhood,
            NodeType.FUNCTION_CALL: self._visit_function,
            NodeType.LITERAL: None,
            NodeType.VARIABLE: None,
            NodeType.IDENTIFIER: None,
        }
        fn = visitor.get(node.node_type)
        if fn:
            fn(node)

    def _visit_select(self, node: SelectNode) -> None:
        if not node.columns:
            self._errors.append(SemanticError("SELECT must have at least one column"))
        for c in node.columns:
            self._visit(c)
        for f in node.filters:
            self._visit(f)
        for j in node.joins:
            self._visit(j)
        for a in node.aggregates:
            self._visit(a)
        for o in node.order:
            self._visit(o)
        for u in node.unions:
            self._visit(u)
        for o in node.optional:
            self._visit(o)
        self._check_mixed_aggregates(node)

    def _check_mixed_aggregates(self, node: SelectNode) -> None:
        has_agg = bool(node.aggregates) or any(
            c.node_type == NodeType.AGGREGATE for c in node.columns
        )
        has_non_agg = any(c.node_type == NodeType.VARIABLE for c in node.columns)
        if has_agg and has_non_agg and not node.aggregates:
            self._errors.append(
                SemanticError("Cannot mix aggregate and non-aggregate columns without GROUP BY")
            )

    def _visit_filter(self, node: FilterNode) -> None:
        if node.condition:
            self._visit(node.condition)

    def _visit_join(self, node: JoinNode) -> None:
        if node.left:
            self._visit(node.left)
        if node.right:
            self._visit(node.right)

    def _visit_projection(self, node: ProjectionNode) -> None:
        for c in node.columns:
            self._visit(c)

    def _visit_aggregate(self, node: AggregateNode) -> None:
        pass

    def _visit_order(self, node: OrderNode) -> None:
        pass

    def _visit_limit(self, node: LimitNode) -> None:
        if node.count < 0:
            self._errors.append(SemanticError("LIMIT must be non-negative"))

    def _visit_union(self, node: UnionNode) -> None:
        if node.left:
            self._visit(node.left)
        if node.right:
            self._visit(node.right)

    def _visit_optional(self, node: OptionalNode) -> None:
        if node.inner:
            self._visit(node.inner)

    def _visit_binary_op(self, node: BinaryOpNode) -> None:
        if node.left:
            self._visit(node.left)
        if node.right:
            self._visit(node.right)

    def _visit_unary_op(self, node: UnaryOpNode) -> None:
        if node.operand:
            self._visit(node.operand)

    def _visit_comparison(self, node: ComparisonNode) -> None:
        if node.left:
            self._visit(node.left)
        if node.right:
            self._visit(node.right)

    def _visit_temporal(self, node: TemporalPredNode) -> None:
        if not node.variable:
            self._errors.append(SemanticError("TEMPORAL predicate requires a variable"))

    def _visit_context(self, node: ContextPredNode) -> None:
        if not node.context:
            self._errors.append(SemanticError("CONTEXT predicate requires a context string"))

    def _visit_provenance(self, node: ProvenancePredNode) -> None:
        if not node.source:
            self._errors.append(SemanticError("PROVENANCE predicate requires a source"))

    def _visit_neighborhood(self, node: NeighborhoodPredNode) -> None:
        if not node.entity:
            self._errors.append(SemanticError("NEIGHBORHOOD predicate requires an entity"))

    def _visit_function(self, node: FunctionCallNode) -> None:
        for a in node.args:
            self._visit(a)


def analyze(node: SelectNode) -> list[SemanticError]:
    return SemanticAnalyzer().analyze(node)
