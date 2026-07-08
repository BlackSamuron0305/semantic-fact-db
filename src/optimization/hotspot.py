"""Hotspot analysis — identifies performance bottlenecks.

Uses the existing Profiler and MeasuredRun infrastructure to
instrument key operations: insert, query, restrict, glue, encode,
decode, scan, join.  Reports the top-K hottest functions by
cumulative time, call count, and memory allocation.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class HotspotEntry:
    name: str
    total_time_ns: int = 0
    call_count: int = 0
    total_memory_bytes: int = 0
    avg_time_ns: float = 0.0

    @property
    def total_time_ms(self) -> float:
        return self.total_time_ns / 1_000_000

    @property
    def avg_time_ms(self) -> float:
        return self.avg_time_ns / 1_000_000

    def merge(self, other: HotspotEntry) -> None:
        self.total_time_ns += other.total_time_ns
        self.call_count += other.call_count
        self.total_memory_bytes += other.total_memory_bytes
        self.avg_time_ns = self.total_time_ns / max(1, self.call_count)


@dataclass
class HotspotReport:
    entries: list[HotspotEntry] = field(default_factory=list)
    total_time_ns: int = 0

    @property
    def total_time_ms(self) -> float:
        return self.total_time_ns / 1_000_000

    def top_k(self, k: int = 10) -> list[HotspotEntry]:
        return sorted(self.entries, key=lambda e: e.total_time_ns, reverse=True)[:k]

    def by_name(self, name: str) -> HotspotEntry | None:
        for e in self.entries:
            if e.name == name:
                return e
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_time_ns": self.total_time_ns,
            "total_time_ms": self.total_time_ms,
            "entries": [
                {
                    "name": e.name,
                    "total_time_ns": e.total_time_ns,
                    "total_time_ms": e.total_time_ms,
                    "call_count": e.call_count,
                    "avg_time_ns": e.avg_time_ns,
                    "avg_time_ms": e.avg_time_ms,
                    "memory_bytes": e.total_memory_bytes,
                }
                for e in self.entries
            ],
        }

    def to_text(self) -> str:
        lines = [
            "Hotspot Analysis Report",
            "=" * 80,
            f"Total time: {self.total_time_ms:.2f} ms",
            "",
            "Top Hotspots",
            "-" * 80,
            f"{'Name':45s}  {'Total (ms)':>12s}  {'Calls':>8s}  {'Avg (ms)':>10s}  {'Memory (KB)':>12s}",
            "-" * 80,
        ]
        for e in self.top_k():
            mem_kb = e.total_memory_bytes / 1024
            lines.append(
                f"{e.name:45s}  {e.total_time_ms:>10.2f}  "
                f"{e.call_count:>8d}  {e.avg_time_ms:>8.4f}  {mem_kb:>10.1f}"
            )
        lines.extend(["", "All Entries", "-" * 60])
        for e in sorted(self.entries, key=lambda x: x.total_time_ns, reverse=True):
            lines.append(f"  {e.name:45s}  {e.total_time_ms:>8.2f} ms  ({e.call_count} calls, {e.avg_time_ms:.3f} ms avg)")
        return "\n".join(lines)


class HotspotProbe:
    """Context manager that records a hotspot sample."""

    def __init__(self, name: str, collector: HotspotCollector) -> None:
        self._name = name
        self._collector = collector
        self._start: int = 0

    def __enter__(self) -> HotspotProbe:
        self._start = time.perf_counter_ns()
        return self

    def __exit__(self, *args: Any) -> None:
        elapsed = time.perf_counter_ns() - self._start
        self._collector.record(self._name, elapsed, memory_bytes=0)


class HotspotCollector:
    """Collects hotspot samples from instrumented code."""

    def __init__(self) -> None:
        self._data: dict[str, HotspotEntry] = {}

    def record(self, name: str, time_ns: int, memory_bytes: int = 0) -> None:
        if name not in self._data:
            self._data[name] = HotspotEntry(name=name)
        self._data[name].total_time_ns += time_ns
        self._data[name].call_count += 1
        self._data[name].total_memory_bytes += memory_bytes
        self._data[name].avg_time_ns = (
            self._data[name].total_time_ns / self._data[name].call_count
        )

    def probe(self, name: str) -> HotspotProbe:
        return HotspotProbe(name, self)

    def report(self) -> HotspotReport:
        total = sum(e.total_time_ns for e in self._data.values())
        return HotspotReport(
            entries=list(self._data.values()),
            total_time_ns=total,
        )

    def clear(self) -> None:
        self._data.clear()

    def merge(self, other: HotspotCollector) -> None:
        for name, entry in other._data.items():
            if name in self._data:
                self._data[name].merge(entry)
            else:
                self._data[name] = entry


class HotspotAnalysis:
    """Runs a benchmark function while collecting hotspot data.

    Wraps a benchmark function and returns the HotspotReport alongside
    the benchmark results.
    """

    def __init__(self, collector: HotspotCollector | None = None) -> None:
        self._collector = collector or HotspotCollector()

    @property
    def collector(self) -> HotspotCollector:
        return self._collector

    def run(self, benchmark_fn: Callable) -> tuple[Any, HotspotReport]:
        try:
            result = benchmark_fn()
        except Exception as exc:
            result = {"error": str(exc)}
        return result, self._collector.report()
