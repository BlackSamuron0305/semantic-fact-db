"""Benchmark collection for query execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class BenchmarkEntry:
    query_text: str
    engine: str
    execution_time_ms: float
    row_count: int
    optimizer_rules: list[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    timestamp: str = ""
    success: bool = True
    error: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class BenchmarkCollector:
    def __init__(self) -> None:
        self._entries: list[BenchmarkEntry] = []

    def record(self, entry: BenchmarkEntry) -> None:
        self._entries.append(entry)

    def all_entries(self) -> list[BenchmarkEntry]:
        return list(self._entries)

    def summary(self) -> dict[str, Any]:
        if not self._entries:
            return {"entries": 0, "message": "no benchmarks recorded"}
        times = [e.execution_time_ms for e in self._entries if e.success]
        return {
            "entries": len(self._entries),
            "successful": sum(1 for e in self._entries if e.success),
            "failed": sum(1 for e in self._entries if not e.success),
            "avg_time_ms": sum(times) / len(times) if times else 0,
            "min_time_ms": min(times) if times else 0,
            "max_time_ms": max(times) if times else 0,
            "total_time_ms": sum(times),
            "engines": list({e.engine for e in self._entries}),
        }

    def export_results(self) -> list[dict]:
        return [
            {
                "query": e.query_text,
                "engine": e.engine,
                "time_ms": e.execution_time_ms,
                "rows": e.row_count,
                "success": e.success,
                "error": e.error,
            }
            for e in self._entries
        ]

    def clear(self) -> None:
        self._entries.clear()
