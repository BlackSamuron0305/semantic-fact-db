"""OptimizationReport — human-readable and machine-parseable reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .state import OptimizationState


@dataclass
class OptimizationReport:
    profile_name: str
    active: bool
    total_optimizations: int
    enabled_count: int
    states: dict[str, OptimizationState]
    elapsed: float

    @property
    def disabled_count(self) -> int:
        return self.total_optimizations - self.enabled_count

    @property
    def enabled_rate(self) -> float:
        return self.enabled_count / max(1, self.total_optimizations)

    def to_text(self) -> str:
        lines = [
            "Optimization Report",
            "=" * 80,
            f"Profile:        {self.profile_name}",
            f"Active:         {self.active}",
            f"Total optimizations: {self.total_optimizations}",
            f"Enabled:        {self.enabled_count} ({self.enabled_rate:.0%})",
            f"Disabled:       {self.disabled_count}",
            f"Elapsed (s):    {self.elapsed:.2f}",
            "",
            "Enabled Optimizations",
            "-" * 80,
        ]
        for name, state in sorted(self.states.items()):
            if state.enabled:
                e = state.entry
                hit_rate = f"{state.hit_rate:.1%}" if state.hit_count + state.miss_count > 0 else "N/A"
                mem = f"{state.memory_estimate_bytes / 1024:.0f} KB" if state.memory_estimate_bytes else "-"
                lines.append(
                    f"  [ON ] {name:45s}  hits={state.hit_count:<5d} "
                    f"misses={state.miss_count:<5d}  hr={hit_rate:<6s}  mem={mem:>8s}"
                )

        lines.extend(["", "Disabled Optimizations", "-" * 60])
        for name, state in sorted(self.states.items()):
            if not state.enabled:
                lines.append(f"  [OFF] {name}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile_name,
            "active": self.active,
            "total_optimizations": self.total_optimizations,
            "enabled_count": self.enabled_count,
            "disabled_count": self.disabled_count,
            "elapsed_seconds": self.elapsed,
            "states": {
                name: {
                    "enabled": s.enabled,
                    "engine": s.entry.engine,
                    "category": s.entry.category,
                    "hits": s.hit_count,
                    "misses": s.miss_count,
                    "hit_rate": s.hit_rate,
                    "memory_bytes": s.memory_estimate_bytes,
                    "error": s.last_error,
                }
                for name, s in self.states.items()
            },
        }

    def to_markdown(self) -> str:
        lines = [
            "# Optimization Report",
            "",
            f"- **Profile:** `{self.profile_name}`",
            f"- **Active:** {self.active}",
            f"- **Total optimizations:** {self.total_optimizations}",
            f"- **Enabled:** {self.enabled_count} ({self.enabled_rate:.0%})",
            f"- **Elapsed:** {self.elapsed:.2f}s",
            "",
            "## Enabled Optimizations",
            "",
            "| Name | Engine | Category | Hits | Misses | Hit Rate | Memory |",
            "|------|--------|----------|------|--------|----------|--------|",
        ]
        for name, state in sorted(self.states.items()):
            if state.enabled:
                e = state.entry
                hr = f"{state.hit_rate:.1%}" if state.hit_count + state.miss_count > 0 else "N/A"
                mem = f"{state.memory_estimate_bytes:,} B" if state.memory_estimate_bytes else "-"
                lines.append(f"| `{name}` | {e.engine} | {e.category} | {state.hit_count} | {state.miss_count} | {hr} | {mem} |")

        lines.extend(["", "## Disabled Optimizations", ""])
        for name, state in sorted(self.states.items()):
            if not state.enabled:
                lines.append(f"- `{name}`")
        return "\n".join(lines)
