"""Lexer / tokenizer for the storage-independent query language."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .errors import LexerError


class TokenType(Enum):
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    FILTER = auto()
    ORDER = auto()
    BY = auto()
    GROUP = auto()
    LIMIT = auto()
    OFFSET = auto()
    COUNT = auto()
    AVG = auto()
    SUM = auto()
    MIN = auto()
    MAX = auto()
    DISTINCT = auto()
    OPTIONAL = auto()
    UNION = auto()
    AS = auto()
    ASC = auto()
    DESC = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()

    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    VARIABLE = auto()

    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    DOT = auto()
    SEMICOLON = auto()
    LBRACE = auto()
    RBRACE = auto()

    TEMPORAL = auto()
    CONTEXT = auto()
    PROVENANCE = auto()
    NEIGHBORHOOD = auto()

    EOF = auto()


KEYWORDS: dict[str, TokenType] = {
    "SELECT": TokenType.SELECT,
    "FROM": TokenType.FROM,
    "WHERE": TokenType.WHERE,
    "FILTER": TokenType.FILTER,
    "ORDER": TokenType.ORDER,
    "BY": TokenType.BY,
    "GROUP": TokenType.GROUP,
    "LIMIT": TokenType.LIMIT,
    "OFFSET": TokenType.OFFSET,
    "COUNT": TokenType.COUNT,
    "AVG": TokenType.AVG,
    "SUM": TokenType.SUM,
    "MIN": TokenType.MIN,
    "MAX": TokenType.MAX,
    "DISTINCT": TokenType.DISTINCT,
    "OPTIONAL": TokenType.OPTIONAL,
    "UNION": TokenType.UNION,
    "AS": TokenType.AS,
    "ASC": TokenType.ASC,
    "DESC": TokenType.DESC,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "IN": TokenType.IN,
    "TRUE": TokenType.TRUE,
    "FALSE": TokenType.FALSE,
    "NULL": TokenType.NULL,
    "TEMPORAL": TokenType.TEMPORAL,
    "CONTEXT": TokenType.CONTEXT,
    "PROVENANCE": TokenType.PROVENANCE,
    "NEIGHBORHOOD": TokenType.NEIGHBORHOOD,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str = ""
    line: int = 0
    col: int = 0

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r})"


class Lexer:
    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0
        self._line = 1
        self._col = 1
        self._tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        self._tokens = []
        while self._pos < len(self._source):
            ch = self._source[self._pos]
            if ch in " \t\r":
                self._advance()
            elif ch == "\n":
                self._line += 1
                self._col = 1
                self._pos += 1
            elif ch == "#":
                self._skip_line()
            elif ch.isalpha() or ch == "_":
                self._read_identifier()
            elif ch.isdigit():
                self._read_number()
            elif ch == "'" or ch == '"':
                self._read_string()
            elif ch == "?":
                self._read_variable()
            elif ch == "=":
                self._emit(TokenType.EQ, "=")
                self._advance()
            elif ch == "!" and self._peek() == "=":
                self._emit(TokenType.NEQ, "!=")
                self._advance(2)
            elif ch == "<" and self._peek() == "=":
                self._emit(TokenType.LTE, "<=")
                self._advance(2)
            elif ch == ">" and self._peek() == "=":
                self._emit(TokenType.GTE, ">=")
                self._advance(2)
            elif ch == "<":
                self._emit(TokenType.LT, "<")
                self._advance()
            elif ch == ">":
                self._emit(TokenType.GT, ">")
                self._advance()
            elif ch == "+":
                self._emit(TokenType.PLUS, "+")
                self._advance()
            elif ch == "-":
                self._emit(TokenType.MINUS, "-")
                self._advance()
            elif ch == "*":
                self._emit(TokenType.STAR, "*")
                self._advance()
            elif ch == "/":
                self._emit(TokenType.SLASH, "/")
                self._advance()
            elif ch == "(":
                self._emit(TokenType.LPAREN, "(")
                self._advance()
            elif ch == ")":
                self._emit(TokenType.RPAREN, ")")
                self._advance()
            elif ch == ",":
                self._emit(TokenType.COMMA, ",")
                self._advance()
            elif ch == ".":
                self._emit(TokenType.DOT, ".")
                self._advance()
            elif ch == "{":
                self._emit(TokenType.LBRACE, "{")
                self._advance()
            elif ch == "}":
                self._emit(TokenType.RBRACE, "}")
                self._advance()
            elif ch == ";":
                self._emit(TokenType.SEMICOLON, ";")
                self._advance()
            else:
                raise LexerError(
                    f"Unexpected character {ch!r}",
                    location=f"{self._line}:{self._col}",
                )
        self._tokens.append(Token(TokenType.EOF, "", self._line, self._col))
        return self._tokens

    def _advance(self, n: int = 1) -> None:
        for _ in range(n):
            if self._pos < len(self._source):
                self._pos += 1
                self._col += 1

    def _peek(self) -> str:
        if self._pos + 1 < len(self._source):
            return self._source[self._pos + 1]
        return ""

    def _emit(self, ttype: TokenType, value: str) -> None:
        self._tokens.append(Token(ttype, value, self._line, self._col))

    def _skip_line(self) -> None:
        while self._pos < len(self._source) and self._source[self._pos] != "\n":
            self._pos += 1

    def _read_identifier(self) -> None:
        start = self._pos
        while self._pos < len(self._source) and (
            self._source[self._pos].isalnum() or self._source[self._pos] == "_"
        ):
            self._advance()
        word = self._source[start : self._pos]
        ttype = KEYWORDS.get(word.upper(), TokenType.IDENTIFIER)
        self._emit(ttype, word)

    def _read_number(self) -> None:
        start = self._pos
        while self._pos < len(self._source) and self._source[self._pos].isdigit():
            self._advance()
        if self._pos < len(self._source) and self._source[self._pos] == ".":
            self._advance()
            while self._pos < len(self._source) and self._source[self._pos].isdigit():
                self._advance()
        self._emit(TokenType.NUMBER, self._source[start : self._pos])

    def _read_string(self) -> None:
        quote = self._source[self._pos]
        start = self._pos
        self._advance()
        while self._pos < len(self._source) and self._source[self._pos] != quote:
            if self._source[self._pos] == "\\":
                self._advance(2)
            else:
                self._advance()
        if self._pos >= len(self._source):
            raise LexerError("Unterminated string", location=f"{self._line}:{self._col}")
        self._advance()
        self._emit(TokenType.STRING, self._source[start + 1 : self._pos - 1])

    def _read_variable(self) -> None:
        start = self._pos
        self._advance()
        while self._pos < len(self._source) and (
            self._source[self._pos].isalnum() or self._source[self._pos] == "_"
        ):
            self._advance()
        self._emit(TokenType.VARIABLE, self._source[start + 1 : self._pos])
