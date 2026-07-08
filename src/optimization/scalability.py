"""Scalability analysis — measures performance across 9 dimensions.

Each dimension is scaled independently while holding others fixed,
producing a performance curve that reveals scaling bottlenecks.

Scaling dimensions:
  1. facts              — total number of SemanticFacts inserted
  2. entities           — distinct entity references
  3. relations          — distinct relation/predicate types
  4. open_sets          — number of open sets in the topology
  5. contexts           — distinct context strings
  6. points_per_set     — average points (fact IDs) per open set
  7. attributes         — average attributes per fact
  8. queries            — number of concurrent/sequential queries
  9. concurrency        — simulated concurrent access
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ScalabilityPoint:
    scale_value: float
    latency_ms: float = 0.0
    memory_bytes: int = 0
    throughput_qps: float = 0.0
    error: str | None = None


@dataclass
class ScalabilityDimension:
    name: str
    unit: str
    points: list[ScalabilityPoint] = field(default_factory=list)

    @property
    def n_points(self) -> int:
        return len(self.points)

    def is_linear(self, tolerance: float = 0.15) -> bool:
        if len(self.points) < 3:
            return True
        ratios = []
        for i in range(1, len(self.points)):
            if self.points[i - 1].scale_value > 0:
                x_ratio = self.points[i].scale_value / self.points[i - 1].scale_value
                y_ratio = self.points[i].latency_ms / max(0.001, self.points[i - 1].latency_ms)
                ratios.append(y_ratio / x_ratio)
        if not ratios:
            return True
        avg_ratio = sum(ratios) / len(ratios)
        return abs(avg_ratio - 1.0) < tolerance

    @property
    def scaling_behavior(self) -> str:
        if self.is_linear():
            return "linear"
        if len(self.points) < 3:
            return "unknown"
        last = self.points[-1]
        first = self.points[0]
        if first.scale_value > 0 and last.latency_ms > 0:
            ratio = (last.latency_ms / first.latency_ms) / (last.scale_value / first.scale_value)
            if ratio > 1.5:
                return "super_linear"
            if ratio < 0.5:
                return "sub_linear"
        return "near_linear"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "unit": self.unit,
            "scaling_behavior": self.scaling_behavior,
            "points": [
                {
                    "scale": p.scale_value,
                    "latency_ms": p.latency_ms,
                    "memory_bytes": p.memory_bytes,
                    "throughput_qps": p.throughput_qps,
                    "error": p.error,
                }
                for p in self.points
            ],
        }


@dataclass
class ScalabilityResult:
    dimensions: list[ScalabilityDimension] = field(default_factory=list)

    def get(self, name: str) -> ScalabilityDimension | None:
        for d in self.dimensions:
            if d.name == name:
                return d
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimensions": [d.to_dict() for d in self.dimensions],
        }


class ScalabilityAnalysis:
    def __init__(
        self,
        setup_fn: Callable[[str, float], None],
        benchmark_fn: Callable,
        teardown_fn: Callable | None = None,
    ) -> None:
        self._setup_fn = setup_fn
        self._benchmark_fn = benchmark_fn
        self._teardown_fn = teardown_fn

    def run(self, dimensions: list[str] | None = None) -> ScalabilityResult:
        result = ScalabilityResult()

        all_dims = self._default_dimensions()
        target_dims = dimensions or list(all_dims.keys())

        for dim_name in target_dims:
            scale_values = all_dims.get(dim_name, [100, 500, 1000, 5000])
            dimension = ScalabilityDimension(name=dim_name, unit=scale_values[0] if isinstance(scale_values[0], str) else "units")

            for scale_val in scale_values:
                self._setup_fn(dim_name, scale_val)
                try:
                    bench_result = self._benchmark_fn()
                    point = ScalabilityPoint(
                        scale_value=float(scale_val) if not isinstance(scale_val, (int, float)) else scale_val,
                        latency_ms=bench_result.get("latency_ms", 0.0),
                        memory_bytes=bench_result.get("memory_bytes", 0),
                        throughput_qps=bench_result.get("throughput_qps", 0.0),
                    )
                except Exception as exc:
                    point = ScalabilityPoint(
                        scale_value=float(scale_val) if not isinstance(scale_val, (int, float)) else scale_val,
                        error=str(exc),
                    )
                dimension.points.append(point)

                if self._teardown_fn:
                    self._teardown_fn()

            result.dimensions.append(dimension)

        return result

    @staticmethod
    def _default_dimensions() -> dict[str, list[float]]:
        return {
            "facts": [100, 500, 1000, 5000, 10000, 50000, 100000],
            "entities": [50, 100, 500, 1000, 5000, 10000],
            "relations": [5, 10, 20, 50, 100],
            "open_sets": [5, 10, 20, 50, 100, 200],
            "contexts": [1, 5, 10, 20, 50],
            "points_per_set": [10, 50, 100, 500, 1000],
            "attributes": [0, 1, 3, 5, 10],
            "queries": [1, 10, 50, 100, 500],
            "concurrency": [1, 2, 4, 8, 16],
        }
