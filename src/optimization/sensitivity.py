"""Sensitivity analysis — measures the effect of varying one parameter.

Each analysis sweeps a parameter across a range and records latency,
memory, and throughput at each point.  Results can be exported for
plotting (the paper's sensitivity figures).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class SensitivityPoint:
    parameter_value: float
    latency_ms: float = 0.0
    memory_bytes: int = 0
    throughput_qps: float = 0.0
    hit_rate: float = 0.0
    error: str | None = None


@dataclass
class SensitivityResult:
    parameter_name: str
    points: list[SensitivityPoint] = field(default_factory=list)

    @property
    def n_points(self) -> int:
        return len(self.points)

    def best_value(self) -> float:
        valid = [p for p in self.points if p.error is None]
        if not valid:
            return 0.0
        best = min(valid, key=lambda p: p.latency_ms)
        return best.parameter_value

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter_name,
            "points": [
                {
                    "value": p.parameter_value,
                    "latency_ms": p.latency_ms,
                    "memory_bytes": p.memory_bytes,
                    "throughput_qps": p.throughput_qps,
                    "hit_rate": p.hit_rate,
                    "error": p.error,
                }
                for p in self.points
            ],
        }


class SensitivityAnalysis:
    """Sweep a single optimisation parameter across a range.

    Typical parameters:
      - cache_size:     10 → 10_000 entries
      - topology_compression_min_shared:  0.1 → 1.0
      - parallel_workers:  1 → 16
      - batch_size:      1 → 10_000
    """

    def __init__(self, benchmark_fn: Callable) -> None:
        self._benchmark_fn = benchmark_fn

    def run(
        self,
        parameter_name: str,
        values: list[float],
        setter: Callable[[float], None],
    ) -> SensitivityResult:
        result = SensitivityResult(parameter_name=parameter_name)

        for val in values:
            setter(val)
            try:
                bench_result = self._benchmark_fn()
                point = SensitivityPoint(
                    parameter_value=val,
                    latency_ms=bench_result.get("latency_ms", 0.0),
                    memory_bytes=bench_result.get("memory_bytes", 0),
                    throughput_qps=bench_result.get("throughput_qps", 0.0),
                    hit_rate=bench_result.get("hit_rate", 0.0),
                )
            except Exception as exc:
                point = SensitivityPoint(
                    parameter_value=val,
                    error=str(exc),
                )
            result.points.append(point)

        return result

    @staticmethod
    def default_sweeps() -> dict[str, list[float]]:
        return OrderedDict({
            "cache_size": [10, 50, 100, 500, 1000, 5000, 10000],
            "batch_size": [1, 10, 50, 100, 500, 1000, 5000],
            "parallel_workers": [1, 2, 4, 8, 16],
            "topology_compression": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            "lru_max_entries": [10, 50, 100, 500, 1000],
            "num_facts": [100, 500, 1000, 5000, 10000, 50000],
            "num_open_sets": [5, 10, 20, 50, 100, 200],
            "points_per_set": [10, 50, 100, 500, 1000],
            "context_count": [1, 5, 10, 20, 50],
            "attribute_count": [0, 1, 3, 5, 10],
        })


from collections import OrderedDict
