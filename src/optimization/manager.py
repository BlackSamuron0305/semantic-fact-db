"""OptimizationManager — central orchestrator.

The manager:
  1. Initialises the registry (if not already done).
  2. Loads a profile (named preset or dict).
  3. Resolves dependencies (enables required dependencies).
  4. Provides hooks that the engines call during execution.
  5. Collects per-optimisation statistics (hit rates, memory, etc.).

Usage::

    mgr = OptimizationManager()
    mgr.load_profile("research")  # or mgr.set("sheaf.restriction_cache", False)
    mgr.activate()
    # ... run benchmarks ...
    report = mgr.report()
"""

from __future__ import annotations

import time
from typing import Any

from .profile import OptimizationProfile, ProfileManager
from .registry import OptimizationRegistry, OptimizationEntry
from .state import OptimizationState
from .report import OptimizationReport


class OptimizationManager:
    def __init__(self) -> None:
        OptimizationRegistry.initialize_defaults()
        self._states: dict[str, OptimizationState] = {}
        self._profile_name: str = "default"
        self._active = False

    # ── Profile loading ─────────────────────────────────────────────

    def load_profile(self, name: str) -> None:
        self._profile_name = name
        profile = ProfileManager.get(name)

        if profile is not None:
            self._apply_profile(profile)
        else:
            self._apply_defaults()

    def _apply_defaults(self) -> None:
        self._states = {}
        for entry in OptimizationRegistry.all():
            state = OptimizationState(entry=entry, enabled=entry.default_on)
            self._states[entry.name] = state

    def _apply_profile(self, profile: OptimizationProfile) -> None:
        self._states = {}
        for entry in OptimizationRegistry.all():
            if entry.name in profile.optimizations:
                enabled = profile.optimizations[entry.name]
            elif profile.strict:
                enabled = False
            else:
                enabled = entry.default_on
            params: dict[str, Any] = {}
            if entry.name in profile.parameters:
                params = profile.parameters[entry.name]
            state = OptimizationState(
                entry=entry,
                enabled=enabled,
            )
            entry.parameters.update(params)
            self._states[entry.name] = state

    def _resolve_dependencies(self) -> None:
        changed = True
        while changed:
            changed = False
            for name, state in self._states.items():
                if state.enabled:
                    for dep in state.entry.dependencies:
                        dep_state = self._states.get(dep)
                        if dep_state is not None and not dep_state.enabled:
                            dep_state.enabled = True
                            changed = True

    # ── Individual control ──────────────────────────────────────────

    def enable(self, name: str) -> None:
        state = self._states.get(name)
        if state is not None:
            state.enabled = True

    def disable(self, name: str) -> None:
        state = self._states.get(name)
        if state is not None:
            state.enabled = False

    def set(self, name: str, enabled: bool) -> None:
        if enabled:
            self.enable(name)
        else:
            self.disable(name)

    def set_parameter(self, name: str, key: str, value: Any) -> None:
        state = self._states.get(name)
        if state is not None:
            state.entry.parameters[key] = value

    def is_enabled(self, name: str) -> bool:
        state = self._states.get(name)
        return state is not None and state.enabled

    # ── Activation ──────────────────────────────────────────────────

    def activate(self) -> None:
        self._resolve_dependencies()
        now = time.time()
        for state in self._states.values():
            if state.enabled:
                state.activated_at = now
        self._active = True

    def deactivate(self) -> None:
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    # ── Statistics hooks ────────────────────────────────────────────

    def record_hit(self, name: str) -> None:
        state = self._states.get(name)
        if state is not None:
            state.record_hit()

    def record_miss(self, name: str) -> None:
        state = self._states.get(name)
        if state is not None:
            state.record_miss()

    def set_memory(self, name: str, bytes_: int) -> None:
        state = self._states.get(name)
        if state is not None:
            state.memory_estimate_bytes = bytes_

    # ── Query helpers ───────────────────────────────────────────────

    def enabled_for_engine(self, engine: str) -> list[OptimizationState]:
        return [
            s for s in self._states.values()
            if s.enabled and s.entry.engine in (engine, "general")
        ]

    def enabled_names(self) -> list[str]:
        return [name for name, s in self._states.items() if s.enabled]

    def all_caches_clear(self) -> None:
        """Hook to clear all caches (called by benchmark runner on cold runs)."""
        pass

    # ── Report ──────────────────────────────────────────────────────

    def report(self) -> OptimizationReport:
        return OptimizationReport(
            profile_name=self._profile_name,
            active=self._active,
            total_optimizations=len(self._states),
            enabled_count=sum(1 for s in self._states.values() if s.enabled),
            states=dict(self._states),
            elapsed=time.time() - (min(s.activated_at for s in self._states.values() if s.enabled) if any(s.enabled for s in self._states.values()) else time.time()),
        )

    # ── Bulk configuration ──────────────────────────────────────────

    def enable_all(self) -> None:
        for state in self._states.values():
            state.enabled = True

    def disable_all(self) -> None:
        for state in self._states.values():
            state.enabled = False

    def enable_category(self, category: str) -> None:
        for state in self._states.values():
            if state.entry.category == category:
                state.enabled = True

    def disable_category(self, category: str) -> None:
        for state in self._states.values():
            if state.entry.category == category:
                state.enabled = False

    def enable_engine(self, engine: str) -> None:
        for state in self._states.values():
            if state.entry.engine == engine:
                state.enabled = True

    def disable_engine(self, engine: str) -> None:
        for state in self._states.values():
            if state.entry.engine == engine:
                state.enabled = False

    def toggle(self, name: str) -> None:
        state = self._states.get(name)
        if state is not None:
            state.enabled = not state.enabled

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self._profile_name,
            "active": self._active,
            "optimizations": {
                name: {
                    "enabled": s.enabled,
                    "hit_rate": s.hit_rate,
                    "hits": s.hit_count,
                    "misses": s.miss_count,
                    "memory_bytes": s.memory_estimate_bytes,
                }
                for name, s in self._states.items()
            },
        }

    def config_snapshot(self) -> dict[str, bool]:
        return {name: s.enabled for name, s in self._states.items()}

    def load_config_snapshot(self, snapshot: dict[str, bool]) -> None:
        for name, enabled in snapshot.items():
            state = self._states.get(name)
            if state is not None:
                state.enabled = enabled
