"""SPARQL-inspired query parser and executor for the Knowledge Graph.

Supports a simplified SPARQL-like syntax:
    SELECT ?var ... WHERE { triple-patterns } FILTER { expr } LIMIT n ORDER BY ?var
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from common.exceptions import QueryError
from common.safe_eval import safe_eval

# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TriplePattern:
    subject: str
    predicate: str
    obj: str


@dataclass(frozen=True)
class FilterExpr:
    expression: str


@dataclass(frozen=True)
class OrderClause:
    variable: str
    ascending: bool = True


@dataclass(frozen=True)
class SparqlQuery:
    select_vars: tuple[str, ...]
    patterns: tuple[TriplePattern, ...]
    filters: tuple[FilterExpr, ...] = field(default_factory=tuple)
    optional_patterns: tuple[TriplePattern, ...] = field(default_factory=tuple)
    limit: int = 0
    offset: int = 0
    order: OrderClause | None = None


# ---------------------------------------------------------------------------
# Tokeniser
# ---------------------------------------------------------------------------

TOKEN_SPEC = [
    ("SELECT", r"SELECT"),
    ("WHERE", r"WHERE"),
    ("FILTER", r"FILTER"),
    ("OPTIONAL", r"OPTIONAL"),
    ("LIMIT", r"LIMIT"),
    ("OFFSET", r"OFFSET"),
    ("ORDER", r"ORDER"),
    ("BY", r"BY"),
    ("ASC", r"ASC"),
    ("DESC", r"DESC"),
    ("DOT", r"\."),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("SEMICOLON", r";"),
    ("VAR", r"\?\w+"),
    ("PREFIX", r"\w+:"),
    ("IRI", r"<[^>]+>"),
    ("STRING", r'"[^"]*"'),
    ("NUMBER", r"\d+(\.\d+)?"),
    ("LANGTAG", r"@\w+"),
    ("TYPE", r"a\b"),
    ("OP", r"[=!<>]+"),
    ("IDENT", r"[a-zA-Z_]\w*"),
    ("WS", r"\s+"),
    ("COMMENT", r"#.*"),
    ("MISC", r"."),
]

TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


@dataclass
class Token:
    kind: str
    value: str
    pos: int


def tokenize(query: str) -> list[Token]:
    tokens: list[Token] = []
    for m in TOKEN_RE.finditer(query):
        kind = m.lastgroup
        assert kind is not None
        value = m.group()
        if kind in ("WS", "COMMENT"):
            continue
        tokens.append(Token(kind=kind, value=value, pos=m.start()))
    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class SparqlParser:
    """Parses a simplified SPARQL query string into a SparqlQuery AST."""

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def peek(self) -> Token | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def consume(self, kind: str | None = None) -> Token:
        tok = self.peek()
        if tok is None:
            raise QueryError("Unexpected end of query")
        if kind is not None and tok.kind != kind:
            raise QueryError(
                f"Expected {kind}, got {tok.kind} ({tok.value}) at position {tok.pos}"
            )
        self._pos += 1
        return tok

    def skip(self, kind: str) -> bool:
        tok = self.peek()
        if tok is not None and tok.kind == kind:
            self._pos += 1
            return True
        return False

    def parse(self) -> SparqlQuery:
        self.consume("SELECT")
        select_vars: list[str] = []
        if self.skip("MISC") and self.peek() and self.peek().value == "*":
            self.consume("MISC")
            select_vars.append("*")
        else:
            while self.peek() and self.peek().kind == "VAR":
                select_vars.append(self.consume("VAR").value)
        self.consume("WHERE")
        self.consume("LBRACE")
        patterns: list[TriplePattern] = []
        filters: list[FilterExpr] = []
        optional_patterns: list[TriplePattern] = []
        while self.peek() and self.peek().kind != "RBRACE":
            if self.skip("OPTIONAL"):
                self.consume("LBRACE")
                while self.peek() and self.peek().kind != "RBRACE":
                    optional_patterns.append(self._parse_triple_pattern())
                self.consume("RBRACE")
            elif self.skip("FILTER"):
                self.consume("LPAREN")
                expr_parts: list[str] = []
                depth = 1
                while self.peek() and depth > 0:
                    if self.peek().kind == "LPAREN":
                        depth += 1
                    if self.peek().kind == "RPAREN":
                        depth -= 1
                        if depth == 0:
                            break
                    expr_parts.append(self.consume().value)
                self.consume("RPAREN")
                filters.append(FilterExpr(" ".join(expr_parts)))
            else:
                patterns.append(self._parse_triple_pattern())
        self.consume("RBRACE")
        order: OrderClause | None = None
        if self.skip("ORDER"):
            self.consume("BY")
            asc = True
            if self.skip("DESC"):
                asc = False
            elif self.skip("ASC"):
                pass
            var = self.consume("VAR").value
            order = OrderClause(variable=var, ascending=asc)
        limit = 0
        if self.skip("LIMIT"):
            limit = int(self.consume("NUMBER").value)
        offset = 0
        if self.skip("OFFSET"):
            offset = int(self.consume("NUMBER").value)
        return SparqlQuery(
            select_vars=tuple(select_vars),
            patterns=tuple(patterns),
            filters=tuple(filters),
            optional_patterns=tuple(optional_patterns),
            limit=limit,
            offset=offset,
            order=order,
        )

    def _parse_triple_pattern(self) -> TriplePattern:
        s = self._parse_term()
        p = self._parse_term()
        o = self._parse_term()
        self.skip("DOT")
        return TriplePattern(subject=s, predicate=p, obj=o)

    def _parse_term(self) -> str:
        tok = self.consume()
        if tok.kind in ("VAR", "IRI", "STRING", "NUMBER", "IDENT", "TYPE"):
            return tok.value
        if tok.kind == "PREFIX":
            suffix = self.consume("IDENT").value
            return f"{tok.value}{suffix}"
        raise QueryError(f"Unexpected token {tok.kind} ({tok.value})")


# ---------------------------------------------------------------------------
# Result set
# ---------------------------------------------------------------------------


@dataclass
class BindingSet:
    bindings: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Query executor
# ---------------------------------------------------------------------------


class SparqlExecutor:
    """Executes a parsed SparqlQuery against triple data.

    This is a naive interpreter that iterates over patterns and binds variables.
    """

    def __init__(self, triples: list[tuple]) -> None:
        self._triples = triples

    def execute(self, query: SparqlQuery) -> list[dict[str, str]]:
        results = self._eval_patterns(query.patterns)
        for opt in query.optional_patterns:
            opt_results = self._eval_patterns((opt,))
            for r in results:
                for o in opt_results:
                    for k, v in o.bindings.items():
                        if k not in r.bindings:
                            r.bindings[k] = v
        if query.filters:
            results = [r for r in results if self._eval_filter(r, query.filters)]
        if query.order is not None:
            rev = not query.order.ascending
            results.sort(key=lambda r: r.bindings.get(query.order.variable, ""), reverse=rev)
        if query.limit > 0:
            results = results[query.offset : query.offset + query.limit]
        seen: set[str] = set()
        unique: list[BindingSet] = []
        for r in results:
            key = str(sorted(r.bindings.items()))
            if key not in seen:
                seen.add(key)
                unique.append(r)
        if query.select_vars == ("*",):
            return [r.bindings for r in unique]
        return [{v: r.bindings.get(v, "") for v in query.select_vars} for r in unique]

    def _eval_patterns(self, patterns: tuple[TriplePattern, ...]) -> list[BindingSet]:
        results: list[BindingSet] = [BindingSet()]
        for pat in patterns:
            new_results: list[BindingSet] = []
            for r in results:
                for t in self._triples:
                    subj, pred, obj, _otype, _ev, _role = t[0], t[1], t[2], t[3], t[4], t[5]
                    match = self._match_triple(pat, subj, pred, obj, r)
                    if match is not None:
                        merged = BindingSet(bindings={**r.bindings, **match})
                        new_results.append(merged)
            results = new_results
            if not results:
                return results
        return results

    def _match_triple(
        self, pat: TriplePattern, s: int, p: int, o: int, bindings: BindingSet
    ) -> dict[str, str] | None:
        mapping: dict[str, str] = {}
        if not self._bind_or_match(pat.subject, str(s), bindings, mapping):
            return None
        if not self._bind_or_match(pat.predicate, str(p), bindings, mapping):
            return None
        if not self._bind_or_match(pat.obj, str(o), bindings, mapping):
            return None
        return mapping

    def _bind_or_match(
        self, pat: str, val: str, bindings: BindingSet, mapping: dict[str, str]
    ) -> bool:
        if pat.startswith("?"):
            var = pat
            existing = bindings.bindings.get(var)
            if existing is not None and existing != val:
                return False
            mapping[var] = val
            return True
        return pat == val or pat.strip('"<>') == val

    def _eval_filter(self, row: BindingSet, filters: tuple[FilterExpr, ...]) -> bool:
        for f in filters:
            expr = f.expression
            for var, val in row.bindings.items():
                expr = expr.replace(var, val)
            try:
                if not safe_eval(expr, {}):
                    return False
            except Exception:
                return False
        return True


def parse_sparql(query_str: str) -> SparqlQuery:
    """Parse a SPARQL query string into an AST."""
    tokens = tokenize(query_str)
    parser = SparqlParser(tokens)
    return parser.parse()
