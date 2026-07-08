"""Profiling — CPU, memory, allocation, GC, disk IO, cache statistics."""

from __future__ import annotations

import gc
import time
from typing import Any


class CacheProfiler:
    def __init__(self) -> None:
        self._hits = 0
        self._misses = 0

    def record_hit(self) -> None:
        self._hits += 1

    def record_miss(self) -> None:
        self._misses += 1

    def hit_rate(self) -> float:
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total

    def stats(self) -> dict[str, Any]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate(),
        }

    def reset(self) -> None:
        self._hits = 0
        self._misses = 0


class AllocationTracker:
    def __init__(self) -> None:
        self._gc_before = 0

    def start(self) -> None:
        gc.collect()
        self._gc_before = sum(gc.get_count())

    def stop(self) -> int:
        return sum(gc.get_count()) - self._gc_before


def measure_cold_cache_overhead(fn: Any, *args: Any, **kwargs: Any) -> float:
    start = time.perf_counter_ns()
    fn(*args, **kwargs)
    return (time.perf_counter_ns() - start) / 1e6


def measure_warm_cache_latency(fn: Any, *args: Any, **kwargs: Any) -> float:
    for _ in range(3):
        fn(*args, **kwargs)
    start = time.perf_counter_ns()
    for _ in range(10):
        fn(*args, **kwargs)
    return (time.perf_counter_ns() - start) / 1e7
