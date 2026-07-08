"""Ablation study framework.

An ablation study measures the contribution of each optimization by
benchmarking with and without it enabled.  Three strategies are
supported:

  1. leave_one_out — disable one optimisation at a time, benchmark each.
  2. pairwise      — disable each pair of optimisations.
  3. random_subset — benchmark random subsets of optimisations (for large N).

Each ablation run produces an AblationResult containing per-optimization
speedup/slowdown data.
"""

from __future__ import annotations

import itertools
import logging
import random
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

from .manager import OptimizationManager


@dataclass
class AblationRun:
    enabled_set: tuple[str, ...]
    disabled_set: tuple[str, ...]
    latency_ms: float = 0.0
    memory_bytes: int = 0
    error: str | None = None


@dataclass
class AblationResult:
    baseline_latency_ms: float = 0.0
    baseline_memory_bytes: int = 0
    runs: list[AblationRun] = field(default_factory=list)

    @property
    def n_runs(self) -> int:
        return len(self.runs)

    def worst_offenders(self, k: int = 5) -> list[AblationRun]:
        sorted_runs = sorted(self.runs, key=lambda r: r.latency_ms, reverse=True)
        return sorted_runs[:k]

    def biggest_improvements(self, k: int = 5) -> list[AblationRun]:
        diff = lambda r: self.baseline_latency_ms - r.latency_ms
        sorted_runs = sorted(self.runs, key=diff, reverse=True)
        return sorted_runs[:k]

    def per_optimization(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for run in self.runs:
            for opt_name in run.disabled_set:
                if opt_name not in result:
                    speedup = self.baseline_latency_ms / max(0.001, run.latency_ms)
                    result[opt_name] = speedup
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_latency_ms": self.baseline_latency_ms,
            "baseline_memory_bytes": self.baseline_memory_bytes,
            "runs": [
                {
                    "enabled": list(r.enabled_set),
                    "disabled": list(r.disabled_set),
                    "latency_ms": r.latency_ms,
                    "memory_bytes": r.memory_bytes,
                    "error": r.error,
                }
                for r in self.runs
            ],
            "per_optimization": self.per_optimization(),
        }


class AblationStudy:
    def __init__(
        self,
        manager: OptimizationManager,
        benchmark_fn: callable,
        strategy: str = "leave_one_out",
        random_seed: int = 42,
    ) -> None:
        self._manager = manager
        self._benchmark_fn = benchmark_fn
        self._strategy = strategy
        self._rng = random.Random(random_seed)

    def run(self, warmup_runs: int = 2) -> AblationResult:
        log = logging.getLogger(__name__)
        baseline_enabled = self._manager.config_snapshot()

        baseline = self._run_benchmark("baseline")
        result = AblationResult(
            baseline_latency_ms=baseline.get("latency_ms", 0.0),
            baseline_memory_bytes=baseline.get("memory_bytes", 0),
        )

        enabled_names = [n for n, v in baseline_enabled.items() if v]
        disabled_names = [n for n, v in baseline_enabled.items() if not v]

        if self._strategy == "leave_one_out":
            candidates = enabled_names
            for opt_name in candidates:
                self._manager.disable(opt_name)
                self._manager.activate()
                run_result = self._run_benchmark(f"ablate_{opt_name}")
                run = AblationRun(
                    enabled_set=tuple(n for n in enabled_names if n != opt_name),
                    disabled_set=(opt_name,),
                    latency_ms=run_result.get("latency_ms", 0.0),
                    memory_bytes=run_result.get("memory_bytes", 0),
                    error=run_result.get("error"),
                )
                result.runs.append(run)
                self._manager.enable(opt_name)

            for opt_name in disabled_names:
                self._manager.enable(opt_name)
                self._manager.activate()
                run_result = self._run_benchmark(f"add_{opt_name}")
                run = AblationRun(
                    enabled_set=tuple(n for n in enabled_names) + (opt_name,),
                    disabled_set=(),
                    latency_ms=run_result.get("latency_ms", 0.0),
                    memory_bytes=run_result.get("memory_bytes", 0),
                    error=run_result.get("error"),
                )
                result.runs.append(run)
                self._manager.disable(opt_name)

        elif self._strategy == "pairwise":
            pairs = list(itertools.combinations(enabled_names, 2))
            for opt_a, opt_b in pairs[:50]:
                self._manager.disable(opt_a)
                self._manager.disable(opt_b)
                self._manager.activate()
                run_result = self._run_benchmark(f"ablate_{opt_a}_{opt_b}")
                run = AblationRun(
                    enabled_set=tuple(n for n in enabled_names if n not in (opt_a, opt_b)),
                    disabled_set=(opt_a, opt_b),
                    latency_ms=run_result.get("latency_ms", 0.0),
                    memory_bytes=run_result.get("memory_bytes", 0),
                    error=run_result.get("error"),
                )
                result.runs.append(run)
                self._manager.enable(opt_a)
                self._manager.enable(opt_b)

        elif self._strategy == "random_subset":
            n = len(enabled_names)
            n_subsets = min(100, 2**n)
            for _ in range(n_subsets):
                subset = tuple(
                    name for name in enabled_names if self._rng.random() < 0.5
                )
                disabled = tuple(n for n in enabled_names if n not in subset)
                if not disabled:
                    continue
                for name in disabled:
                    self._manager.disable(name)
                self._manager.activate()
                run_result = self._run_benchmark(f"random_{len(disabled)}_off")
                run = AblationRun(
                    enabled_set=subset,
                    disabled_set=disabled,
                    latency_ms=run_result.get("latency_ms", 0.0),
                    memory_bytes=run_result.get("memory_bytes", 0),
                    error=run_result.get("error"),
                )
                result.runs.append(run)
                for name in disabled:
                    self._manager.enable(name)

        self._manager.load_config_snapshot(baseline_enabled)
        self._manager.activate()
        return result

    def _run_benchmark(self, tag: str) -> dict[str, Any]:
        try:
            result = self._benchmark_fn()
            if isinstance(result, dict):
                return result
            return {"latency_ms": 0.0, "memory_bytes": 0}
        except Exception as exc:
            logging.warning("Ablation run '%s' failed: %s", tag, exc)
            return {"latency_ms": float("nan"), "memory_bytes": 0, "error": str(exc)}
