"""Statistics collection for query optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TableStatistics:
    row_count: int = 0
    distinct_values: dict[str, int] = field(default_factory=dict)
    null_fraction: dict[str, float] = field(default_factory=dict)
    min_value: dict[str, Any] = field(default_factory=dict)
    max_value: dict[str, Any] = field(default_factory=dict)
    avg_width: dict[str, float] = field(default_factory=dict)


class StatisticsStore:
    def __init__(self) -> None:
        self._tables: dict[str, TableStatistics] = {}

    def register(self, name: str, stats: TableStatistics) -> None:
        self._tables[name] = stats

    def get(self, name: str) -> TableStatistics | None:
        return self._tables.get(name)

    def update_row_count(self, name: str, count: int) -> None:
        if name in self._tables:
            self._tables[name].row_count = count

    def update_distinct(self, name: str, column: str, count: int) -> None:
        if name in self._tables:
            self._tables[name].distinct_values[column] = count

    def estimate_selectivity(self, name: str, column: str) -> float:
        stats = self._tables.get(name)
        if stats is None:
            return 0.5
        distinct = stats.distinct_values.get(column, 1)
        if stats.row_count == 0:
            return 0.5
        return min(1.0, 1.0 / distinct)

    def all_stats(self) -> dict[str, dict]:
        return {
            name: {
                "row_count": t.row_count,
                "distinct_values": t.distinct_values,
                "null_fraction": t.null_fraction,
            }
            for name, t in self._tables.items()
        }
