"""OptimizationState — mutable state for a single optimization.

Separated from manager.py to avoid circular imports with report.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .registry import OptimizationEntry


@dataclass
class OptimizationState:
    entry: OptimizationEntry
    enabled: bool = True
    activated_at: float = 0.0
    hit_count: int = 0
    miss_count: int = 0
    memory_estimate_bytes: int = 0
    last_error: str | None = None

    @property
    def hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0

    def record_hit(self) -> None:
        self.hit_count += 1

    def record_miss(self) -> None:
        self.miss_count += 1
