"""Base class for optimization modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OptimizationHook:
    """Record-keeping for optimization statistics.

    Engines call hook.hit() / hook.miss() when the optimisation
    is exercised.  The manager collects these for reports.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.hits = 0
        self.misses = 0

    def hit(self) -> None:
        self.hits += 1

    def miss(self) -> None:
        self.misses += 1

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def reset(self) -> None:
        self.hits = 0
        self.misses = 0


class BaseOptimization(ABC):
    """Abstract base for all optimization modules.

    Subclasses implement:
      - name:        unique identifier matching the registry entry
      - enable():    activate the optimisation
      - disable():   deactivate the optimisation
      - is_enabled:  property returning current state
      - reset():     clear internal state (caches, counters)
    """

    def __init__(self) -> None:
        self._enabled = True
        self._hook = OptimizationHook(self.name)

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def hook(self) -> OptimizationHook:
        return self._hook

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False
        self.reset()

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def reset(self) -> None:
        self._hook.reset()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "enabled": self._enabled,
            "hits": self._hook.hits,
            "misses": self._hook.misses,
            "hit_rate": self._hook.hit_rate,
        }


class NullOptimization(BaseOptimization):
    """No-op optimisation (for testing)."""

    @property
    def name(self) -> str:
        return "null"
