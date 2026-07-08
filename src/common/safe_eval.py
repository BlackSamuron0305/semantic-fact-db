"""Safe expression evaluator using AST whitelisting.

Replaces all uses of eval() with a restricted evaluator that only
permits a whitelisted set of AST node types (comparisons, booleans,
arithmetic, literals, and variable references).
"""

from __future__ import annotations

import ast
from typing import Any

_ALLOWED_NODES = frozenset({
    ast.Expression,
    ast.Constant,
    ast.Name,
    ast.UnaryOp,
    ast.BinOp,
    ast.BoolOp,
    ast.Compare,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    ast.And,
    ast.Or,
    ast.Mod,
    ast.Pow,
    ast.FloorDiv,
})


class _UnsafeExpression(ValueError):
    pass


def safe_eval(
    expression: str,
    variables: dict[str, Any],
) -> Any:
    """Evaluate a simple expression with only whitelisted operations.

    Args:
        expression: The expression string to evaluate.
        variables: Dict of variable name -> value for Name lookups.

    Returns:
        The evaluated result.

    Raises:
        _UnsafeExpression: If the expression uses disallowed AST nodes.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise _UnsafeExpression(f"Syntax error in expression: {expression!r}") from None

    if not isinstance(tree, ast.Expression):
        raise _UnsafeExpression(f"Expected expression, got {type(tree).__name__}")

    return _eval_node(tree.body, variables)


def _eval_node(node: ast.AST, variables: dict[str, Any]) -> Any:
    """Recursively evaluate an AST node with whitelist checking."""
    node_type = type(node)

    if node_type not in _ALLOWED_NODES:
        raise _UnsafeExpression(
            f"Expression uses disallowed construct: {node_type.__name__} "
            f"at line {getattr(node, 'lineno', '?')}"
        )

    if node_type is ast.Constant:
        return node.value

    if node_type is ast.Name:
        name = node.id
        if name not in variables:
            raise NameError(f"Variable {name!r} is not bound")
        return variables[name]

    if node_type is ast.UnaryOp:
        operand = _eval_node(node.operand, variables)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise _UnsafeExpression(f"Unknown unary operator: {type(node.op).__name__}")

    if node_type is ast.BinOp:
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            return left**right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        raise _UnsafeExpression(f"Unknown binary operator: {type(node.op).__name__}")

    if node_type is ast.BoolOp:
        values = [_eval_node(v, variables) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise _UnsafeExpression(f"Unknown boolean operator: {type(node.op).__name__}")

    if node_type is ast.Compare:
        left = _eval_node(node.left, variables)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, variables)
            if isinstance(op, ast.Eq):
                if not left == right:
                    return False
            elif isinstance(op, ast.NotEq):
                if not left != right:
                    return False
            elif isinstance(op, ast.Lt):
                if not left < right:
                    return False
            elif isinstance(op, ast.LtE):
                if not left <= right:
                    return False
            elif isinstance(op, ast.Gt):
                if not left > right:
                    return False
            elif isinstance(op, ast.GtE):
                if not left >= right:
                    return False
            elif isinstance(op, ast.Is):
                if left is not right:
                    return False
            elif isinstance(op, ast.IsNot):
                if left is right:
                    return False
            elif isinstance(op, ast.In):
                if left not in right:
                    return False
            elif isinstance(op, ast.NotIn):
                if left in right:
                    return False
            else:
                raise _UnsafeExpression(f"Unknown comparison operator: {type(op).__name__}")
            left = right
        return True

    raise _UnsafeExpression(f"Unhandled node type: {node_type.__name__}")
