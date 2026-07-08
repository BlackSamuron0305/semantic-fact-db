"""Query pipeline error types."""

from __future__ import annotations


class QueryError(Exception):
    def __init__(self, message: str, location: str = "", query: str = "", suggestion: str = ""):
        self.message = message
        self.location = location
        self.query = query
        self.suggestion = suggestion
        super().__init__(self._format())

    def _format(self) -> str:
        parts = [self.message]
        if self.location:
            parts.append(f"at {self.location}")
        if self.query:
            parts.append(f"\n  query: {self.query}")
        if self.suggestion:
            parts.append(f"\n  hint: {self.suggestion}")
        return " | ".join(parts)


class LexerError(QueryError):
    pass


class ParseError(QueryError):
    pass


class SemanticError(QueryError):
    pass


class OptimizationError(QueryError):
    pass


class ExecutionError(QueryError):
    pass
