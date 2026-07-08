"""Contextual benchmark metrics — extends SystemMetrics for contextual workloads."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from sfdb.benchmark.metrics import SystemMetrics, MeasuredRun


@dataclass
class ContextualMetrics:
    latency_ms: float = 0.0
    memory_bytes: int = 0
    cpu_percent: float = 0.0
    result_count: int = 0
    result_size_bytes: int = 0
    context_visits: int = 0
    entity_traversals: int = 0
    restriction_map_calls: int = 0
    gluing_operations: int = 0
    consistency_checks: int = 0
    error_count: int = 0

    def to_system_metrics(self) -> SystemMetrics:
        return SystemMetrics(
            latency_ns=int(self.latency_ms * 1_000_000),
            memory_bytes=self.memory_bytes,
            cpu_percent=self.cpu_percent,
        )

    @staticmethod
    def from_system_metrics(sm: SystemMetrics, **extra: Any) -> ContextualMetrics:
        return ContextualMetrics(
            latency_ms=sm.latency_ms,
            memory_bytes=sm.memory_bytes,
            cpu_percent=sm.cpu_percent,
            result_count=extra.get("result_count", 0),
            result_size_bytes=extra.get("result_size_bytes", 0),
            context_visits=extra.get("context_visits", 0),
            entity_traversals=extra.get("entity_traversals", 0),
            restriction_map_calls=extra.get("restriction_map_calls", 0),
            gluing_operations=extra.get("gluing_operations", 0),
            consistency_checks=extra.get("consistency_checks", 0),
            error_count=extra.get("error_count", 0),
        )


def collect_contextual_metrics(
    fn: Callable[[Any], list[dict[str, Any]]],
    params: Any,
    num_warmup: int = 2,
    num_timed: int = 5,
) -> ContextualMetrics:
    """Run a benchmark function and collect contextual metrics."""
    latencies: list[float] = []
    for _ in range(num_warmup):
        fn(params)

    for _ in range(num_timed):
        t0 = time.perf_counter()
        result = fn(params)
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)

    result = fn(params) if not result else result
    result_size = sum(_estimate_row_size(r) for r in result) if result else 0

    return ContextualMetrics(
        latency_ms=sum(latencies) / len(latencies) if latencies else 0.0,
        memory_bytes=0,
        cpu_percent=0.0,
        result_count=len(result),
        result_size_bytes=result_size,
    )


def _estimate_row_size(row: dict[str, Any]) -> int:
    total = 0
    for k, v in row.items():
        total += len(str(k)) + len(str(v))
    return total
