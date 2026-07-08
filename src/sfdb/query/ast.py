"""Immutable AST nodes for the query language."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class NodeType(Enum):
    SELECT = auto()
    FILTER = auto()
    JOIN = auto()
    AGGREGATE = auto()
    PROJECTION = auto()
    ORDER = auto()
    LIMIT = auto()
    UNION = auto()
    OPTIONAL = auto()
    BINARY_OP = auto()
    UNARY_OP = auto()
    LITERAL = auto()
    VARIABLE = auto()
    FUNCTION_CALL = auto()
    COMPARISON = auto()
    TEMPORAL_PRED = auto()
    CONTEXT_PRED = auto()
    PROVENANCE_PRED = auto()
    NEIGHBORHOOD_PRED = auto()
    IDENTIFIER = auto()


class BinaryOp(Enum):
    EQ = "="
    NEQ = "!="
    LT = "<"
    GT = ">"
    LTE = "<="
    GTE = ">="
    AND = "AND"
    OR = "OR"
    PLUS = "+"
    MINUS = "-"
    TIMES = "*"
    DIVIDE = "/"


class UnaryOp(Enum):
    NOT = "NOT"
    NEG = "-"
    IS_NULL = "IS NULL"


class Aggregate(Enum):
    COUNT = "COUNT"
    AVG = "AVG"
    SUM = "SUM"
    MIN = "MIN"
    MAX = "MAX"


class OrderDirection(Enum):
    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True)
class ASTNode:
    node_type: NodeType
    location: str = ""


@dataclass(frozen=True)
class LiteralNode(ASTNode):
    value: Any = None
    type_hint: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.LITERAL)


@dataclass(frozen=True)
class VariableNode(ASTNode):
    name: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.VARIABLE)


@dataclass(frozen=True)
class IdentifierNode(ASTNode):
    value: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.IDENTIFIER)


@dataclass(frozen=True)
class BinaryOpNode(ASTNode):
    op: BinaryOp = BinaryOp.EQ
    left: ASTNode | None = None
    right: ASTNode | None = None

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.BINARY_OP)


@dataclass(frozen=True)
class UnaryOpNode(ASTNode):
    op: UnaryOp = UnaryOp.NOT
    operand: ASTNode | None = None

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.UNARY_OP)


@dataclass(frozen=True)
class ComparisonNode(ASTNode):
    op: BinaryOp = BinaryOp.EQ
    left: ASTNode | None = None
    right: ASTNode | None = None

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.COMPARISON)


@dataclass(frozen=True)
class FilterNode(ASTNode):
    condition: ASTNode | None = None

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.FILTER)


@dataclass(frozen=True)
class JoinNode(ASTNode):
    left: ASTNode | None = None
    right: ASTNode | None = None
    condition: ASTNode | None = None
    join_type: str = "inner"

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.JOIN)


@dataclass(frozen=True)
class ProjectionNode(ASTNode):
    columns: tuple[ASTNode, ...] = ()
    distinct: bool = False

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.PROJECTION)


@dataclass(frozen=True)
class AggregateNode(ASTNode):
    function: Aggregate = Aggregate.COUNT
    column: ASTNode | None = None
    alias: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.AGGREGATE)


@dataclass(frozen=True)
class OrderNode(ASTNode):
    column: ASTNode | None = None
    direction: OrderDirection = OrderDirection.ASC

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.ORDER)


@dataclass(frozen=True)
class LimitNode(ASTNode):
    count: int = 0
    offset: int = 0

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.LIMIT)


@dataclass(frozen=True)
class UnionNode(ASTNode):
    left: ASTNode | None = None
    right: ASTNode | None = None

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.UNION)


@dataclass(frozen=True)
class OptionalNode(ASTNode):
    inner: ASTNode | None = None

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.OPTIONAL)


@dataclass(frozen=True)
class TemporalPredNode(ASTNode):
    variable: str = ""
    start: str = ""
    end: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.TEMPORAL_PRED)


@dataclass(frozen=True)
class ContextPredNode(ASTNode):
    variable: str = ""
    context: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.CONTEXT_PRED)


@dataclass(frozen=True)
class ProvenancePredNode(ASTNode):
    variable: str = ""
    source: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.PROVENANCE_PRED)


@dataclass(frozen=True)
class NeighborhoodPredNode(ASTNode):
    variable: str = ""
    entity: str = ""

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.NEIGHBORHOOD_PRED)


@dataclass(frozen=True)
class FunctionCallNode(ASTNode):
    name: str = ""
    args: tuple[ASTNode, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.FUNCTION_CALL)


@dataclass(frozen=True)
class SelectNode(ASTNode):
    columns: tuple[ASTNode, ...] = ()
    source: ASTNode | None = None
    filters: tuple[ASTNode, ...] = ()
    joins: tuple[ASTNode, ...] = ()
    aggregates: tuple[ASTNode, ...] = ()
    order: tuple[ASTNode, ...] = ()
    limit: ASTNode | None = None
    distinct: bool = False
    unions: tuple[ASTNode, ...] = ()
    optional: tuple[ASTNode, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "node_type", NodeType.SELECT)
