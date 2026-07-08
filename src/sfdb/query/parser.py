"""Recursive descent parser generating immutable AST nodes."""

from __future__ import annotations

from .ast import (
    Aggregate,
    AggregateNode,
    ASTNode,
    BinaryOp,
    BinaryOpNode,
    ComparisonNode,
    ContextPredNode,
    FunctionCallNode,
    IdentifierNode,
    JoinNode,
    LimitNode,
    LiteralNode,
    NeighborhoodPredNode,
    NodeType,
    OptionalNode,
    OrderDirection,
    OrderNode,
    ProjectionNode,
    ProvenancePredNode,
    SelectNode,
    TemporalPredNode,
    UnaryOp,
    UnaryOpNode,
    VariableNode,
)
from .errors import ParseError
from .lexer import Lexer, Token, TokenType


class Parser:
    def __init__(self, source: str) -> None:
        self._tokens = Lexer(source).tokenize()
        self._pos = 0

    def parse(self) -> ASTNode:
        result = self._parse_select()
        if self._peek().type != TokenType.EOF:
            raise ParseError("Unexpected token after SELECT", location=str(self._peek().line))
        return result

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        t = self._tokens[self._pos]
        self._pos += 1
        return t

    def _expect(self, ttype: TokenType) -> Token:
        if self._peek().type != ttype:
            got = self._peek().type.name
            raise ParseError(
                f"Expected {ttype.name}, got {got}",
                location=f"{self._peek().line}:{self._peek().col}",
            )
        return self._advance()

    def _parse_select(self) -> SelectNode:
        self._expect(TokenType.SELECT)
        distinct = False
        if self._peek().type == TokenType.DISTINCT:
            self._advance()
            distinct = True

        columns: list[ASTNode] = []
        if self._peek().type == TokenType.STAR:
            self._advance()
            columns.append(VariableNode(node_type=NodeType.VARIABLE, name="*"))
        else:
            columns.append(self._parse_projection_column())
            while self._peek().type == TokenType.COMMA:
                self._advance()
                columns.append(self._parse_projection_column())

        self._expect(TokenType.FROM)
        source = IdentifierNode(
            node_type=NodeType.IDENTIFIER, value=self._expect(TokenType.IDENTIFIER).value
        )

        filters: list[ASTNode] = []
        joins: list[ASTNode] = []
        aggregates: list[ASTNode] = []
        order: list[ASTNode] = []
        limit: ASTNode | None = None
        unions: list[ASTNode] = []
        optional: list[ASTNode] = []

        while self._peek().type not in (TokenType.EOF, TokenType.SEMICOLON):
            t = self._peek().type
            if t == TokenType.WHERE:
                self._advance()
                filters.append(self._parse_condition())
                while self._peek().type in (TokenType.AND, TokenType.OR):
                    self._advance()
                    filters.append(self._parse_condition())
            elif t == TokenType.FILTER:
                self._advance()
                self._expect(TokenType.LPAREN)
                filters.append(self._parse_condition())
                self._expect(TokenType.RPAREN)
            elif t == TokenType.TEMPORAL:
                self._advance()
                self._expect(TokenType.LPAREN)
                var = self._expect(TokenType.VARIABLE).value
                self._expect(TokenType.COMMA)
                start = self._expect(TokenType.STRING).value
                self._expect(TokenType.COMMA)
                end = self._expect(TokenType.STRING).value
                self._expect(TokenType.RPAREN)
                filters.append(
                    TemporalPredNode(
                        node_type=NodeType.TEMPORAL_PRED, variable=var, start=start, end=end
                    )
                )
            elif t == TokenType.CONTEXT:
                self._advance()
                self._expect(TokenType.LPAREN)
                var = self._expect(TokenType.VARIABLE).value
                self._expect(TokenType.COMMA)
                ctx = self._expect(TokenType.STRING).value
                self._expect(TokenType.RPAREN)
                filters.append(
                    ContextPredNode(node_type=NodeType.CONTEXT_PRED, variable=var, context=ctx)
                )
            elif t == TokenType.PROVENANCE:
                self._advance()
                self._expect(TokenType.LPAREN)
                var = self._expect(TokenType.VARIABLE).value
                self._expect(TokenType.COMMA)
                src = self._expect(TokenType.STRING).value
                self._expect(TokenType.RPAREN)
                filters.append(
                    ProvenancePredNode(
                        node_type=NodeType.PROVENANCE_PRED, variable=var, source=src
                    )
                )
            elif t == TokenType.NEIGHBORHOOD:
                self._advance()
                self._expect(TokenType.LPAREN)
                var = self._expect(TokenType.VARIABLE).value
                self._expect(TokenType.COMMA)
                ent = self._expect(TokenType.STRING).value
                self._expect(TokenType.RPAREN)
                filters.append(
                    NeighborhoodPredNode(
                        node_type=NodeType.NEIGHBORHOOD_PRED, variable=var, entity=ent
                    )
                )
            elif t == TokenType.JOIN or t == TokenType.INNER:
                self._advance()
                j = self._parse_join()
                joins.append(j)
            elif t == TokenType.OPTIONAL:
                self._advance()
                opt = self._parse_optional()
                optional.append(opt)
            elif t == TokenType.UNION:
                self._advance()
                unions.append(self._parse_select())
            elif t == TokenType.ORDER:
                self._advance()
                self._expect(TokenType.BY)
                order.append(self._parse_order_column())
                while self._peek().type == TokenType.COMMA:
                    self._advance()
                    order.append(self._parse_order_column())
            elif t == TokenType.GROUP:
                self._advance()
                self._expect(TokenType.BY)
                aggregates.append(self._parse_aggregate())
            elif t == TokenType.LIMIT:
                self._advance()
                cnt = int(self._expect(TokenType.NUMBER).value)
                off = 0
                if self._peek().type == TokenType.OFFSET:
                    self._advance()
                    off = int(self._expect(TokenType.NUMBER).value)
                limit = LimitNode(node_type=NodeType.LIMIT, count=cnt, offset=off)
            else:
                break

        return SelectNode(
            node_type=NodeType.SELECT,
            columns=tuple(columns),
            source=source,
            filters=tuple(filters),
            joins=tuple(joins),
            aggregates=tuple(aggregates),
            order=tuple(order),
            limit=limit,
            distinct=distinct,
            unions=tuple(unions),
            optional=tuple(optional),
        )

    def _parse_projection_column(self) -> ASTNode:
        if self._peek().type == TokenType.COUNT:
            return self._parse_aggregate()
        t = self._peek()
        if t.type == TokenType.VARIABLE:
            v = VariableNode(node_type=NodeType.VARIABLE, name=self._advance().value)
            if self._peek().type == TokenType.DOT:
                self._advance()
                attr = self._expect(TokenType.IDENTIFIER).value
                return FunctionCallNode(
                    node_type=NodeType.FUNCTION_CALL,
                    name="attr",
                    args=(v, IdentifierNode(node_type=NodeType.IDENTIFIER, value=attr)),
                )
            if self._peek().type == TokenType.AS:
                self._advance()
                self._expect(TokenType.IDENTIFIER).value
                return ProjectionNode(node_type=NodeType.PROJECTION, columns=(v,), distinct=False)
            return v
        if t.type == TokenType.IDENTIFIER:
            return IdentifierNode(node_type=NodeType.IDENTIFIER, value=self._advance().value)
        raise ParseError(f"Expected column, got {t.type.name}", location=f"{t.line}:{t.col}")

    def _parse_condition(self) -> ASTNode:
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._peek().type == TokenType.OR:
            self._advance()
            right = self._parse_and()
            left = BinaryOpNode(
                node_type=NodeType.BINARY_OP, op=BinaryOp.OR, left=left, right=right
            )
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_comparison()
        while self._peek().type == TokenType.AND:
            self._advance()
            right = self._parse_comparison()
            left = BinaryOpNode(
                node_type=NodeType.BINARY_OP, op=BinaryOp.AND, left=left, right=right
            )
        return left

    def _parse_comparison(self) -> ASTNode:
        if self._peek().type == TokenType.NOT:
            self._advance()
            return UnaryOpNode(
                node_type=NodeType.UNARY_OP, op=UnaryOp.NOT, operand=self._parse_comparison()
            )
        left = self._parse_primary()
        t = self._peek().type
        if t in (
            TokenType.EQ,
            TokenType.NEQ,
            TokenType.LT,
            TokenType.GT,
            TokenType.LTE,
            TokenType.GTE,
        ):
            op_map = {
                TokenType.EQ: BinaryOp.EQ,
                TokenType.NEQ: BinaryOp.NEQ,
                TokenType.LT: BinaryOp.LT,
                TokenType.GT: BinaryOp.GT,
                TokenType.LTE: BinaryOp.LTE,
                TokenType.GTE: BinaryOp.GTE,
            }
            op = op_map[t]
            self._advance()
            right = self._parse_primary()
            return ComparisonNode(node_type=NodeType.COMPARISON, op=op, left=left, right=right)
        if t == TokenType.IN:
            self._advance()
            self._expect(TokenType.LPAREN)
            items = [self._parse_primary()]
            while self._peek().type == TokenType.COMMA:
                self._advance()
                items.append(self._parse_primary())
            self._expect(TokenType.RPAREN)
            return FunctionCallNode(
                node_type=NodeType.FUNCTION_CALL, name="IN", args=(left, *items)
            )
        return left

    def _parse_primary(self) -> ASTNode:
        t = self._peek()
        if t.type == TokenType.VARIABLE:
            v = VariableNode(node_type=NodeType.VARIABLE, name=self._advance().value)
            if self._peek().type == TokenType.DOT:
                self._advance()
                attr = self._expect(TokenType.IDENTIFIER).value
                return FunctionCallNode(
                    node_type=NodeType.FUNCTION_CALL,
                    name="attr",
                    args=(v, IdentifierNode(node_type=NodeType.IDENTIFIER, value=attr)),
                )
            return v
        if t.type == TokenType.STRING:
            return LiteralNode(
                node_type=NodeType.LITERAL, value=self._advance().value, type_hint="string"
            )
        if t.type == TokenType.NUMBER:
            val = self._advance().value
            return LiteralNode(
                node_type=NodeType.LITERAL,
                value=int(val) if "." not in val else float(val),
                type_hint="number",
            )
        if t.type == TokenType.TRUE:
            self._advance()
            return LiteralNode(node_type=NodeType.LITERAL, value=True, type_hint="bool")
        if t.type == TokenType.FALSE:
            self._advance()
            return LiteralNode(node_type=NodeType.LITERAL, value=False, type_hint="bool")
        if t.type == TokenType.NULL:
            self._advance()
            return LiteralNode(node_type=NodeType.LITERAL, value=None, type_hint="null")
        if t.type == TokenType.IDENTIFIER:
            return IdentifierNode(node_type=NodeType.IDENTIFIER, value=self._advance().value)
        if t.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_condition()
            self._expect(TokenType.RPAREN)
            return expr
        if t.type == TokenType.MINUS:
            self._advance()
            return UnaryOpNode(
                node_type=NodeType.UNARY_OP, op=UnaryOp.NEG, operand=self._parse_primary()
            )
        raise ParseError(f"Unexpected token {t.type.name}", location=f"{t.line}:{t.col}")

    def _parse_join(self) -> JoinNode:
        if self._peek().type == TokenType.IDENTIFIER:
            target = IdentifierNode(
                node_type=NodeType.IDENTIFIER, value=self._expect(TokenType.IDENTIFIER).value
            )
        else:
            target = self._parse_select()
        on_cond: ASTNode | None = None
        if self._peek().type == TokenType.ON:
            self._advance()
            on_cond = self._parse_condition()
        return JoinNode(node_type=NodeType.JOIN, right=target, condition=on_cond)

    def _parse_optional(self) -> OptionalNode:
        inner = self._parse_select()
        return OptionalNode(node_type=NodeType.OPTIONAL, inner=inner)

    def _parse_order_column(self) -> OrderNode:
        col = self._parse_primary()
        direction = OrderDirection.ASC
        if self._peek().type == TokenType.ASC:
            self._advance()
        elif self._peek().type == TokenType.DESC:
            self._advance()
            direction = OrderDirection.DESC
        return OrderNode(node_type=NodeType.ORDER, column=col, direction=direction)

    def _parse_aggregate(self) -> AggregateNode:
        t = self._peek()
        agg_map = {
            TokenType.COUNT: Aggregate.COUNT,
            TokenType.AVG: Aggregate.AVG,
            TokenType.SUM: Aggregate.SUM,
            TokenType.MIN: Aggregate.MIN,
            TokenType.MAX: Aggregate.MAX,
        }
        func = agg_map.get(t.type)
        if func is None:
            raise ParseError(
                f"Expected aggregate, got {t.type.name}", location=f"{t.line}:{t.col}"
            )
        self._advance()
        self._expect(TokenType.LPAREN)
        col = self._parse_primary()
        self._expect(TokenType.RPAREN)
        alias = ""
        if self._peek().type == TokenType.AS:
            self._advance()
            alias = self._expect(TokenType.IDENTIFIER).value
        return AggregateNode(node_type=NodeType.AGGREGATE, function=func, column=col, alias=alias)


def parse(source: str) -> SelectNode:
    return Parser(source).parse()
