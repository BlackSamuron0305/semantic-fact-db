"""Canonical result format — storage-engine agnostic query results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sfdb.common.types import Value


@dataclass(frozen=True)
class CanonicalColumn:
    name: str
    data_type: str = "string"


@dataclass(frozen=True)
class CanonicalRow:
    values: tuple[Value, ...]
    score: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalResult:
    columns: tuple[CanonicalColumn, ...]
    rows: tuple[CanonicalRow, ...]
    row_count: int = 0
    execution_time_ms: float = 0.0
    engine_hint: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "row_count", len(self.rows))

    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def to_dicts(self) -> list[dict[str, Any]]:
        names = self.column_names()
        return [
            {
                names[i]: row.values[i].inner if i < len(row.values) else None
                for i in range(len(names))
            }
            for row in self.rows
        ]

    def to_pretty_string(self, max_rows: int = 20) -> str:
        if not self.columns:
            return "(empty result)"

        col_names = self.column_names()
        col_widths = [len(n) for n in col_names]
        data_rows: list[list[str]] = []
        for row in self.rows[:max_rows]:
            r: list[str] = []
            for i, v in enumerate(row.values):
                s = str(v.inner) if v.inner is not None else "NULL"
                r.append(s)
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(s))
            data_rows.append(r)

        sep = "+".join("-" * (w + 2) for w in col_widths)
        header = "| " + " | ".join(n.ljust(w) for n, w in zip(col_names, col_widths, strict=False)) + " |"

        lines: list[str] = []
        lines.append(sep)
        lines.append(header)
        lines.append(sep.replace("-", "="))
        for r in data_rows:
            row_str = "| " + " | ".join(s.ljust(w) for s, w in zip(r, col_widths, strict=False)) + " |"
            lines.append(row_str)
        lines.append(sep)

        if len(self.rows) > max_rows:
            lines.append(f"... and {len(self.rows) - max_rows} more rows")

        lines.append(f"\n({len(self.rows)} row(s) in {self.execution_time_ms:.1f}ms)")
        return "\n".join(lines)

    def __add__(self, other: CanonicalResult) -> CanonicalResult:
        if self.columns != other.columns:
            cols = self.columns + tuple(c for c in other.columns if c not in self.columns)
        else:
            cols = self.columns
        return CanonicalResult(
            columns=cols,
            rows=self.rows + other.rows,
            engine_hint=f"{self.engine_hint}+{other.engine_hint}",
        )
