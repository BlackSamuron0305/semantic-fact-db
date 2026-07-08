"""Named configuration profiles for the optimization framework.

Each profile is a named preset that specifies:
  - Which optimizations to enable/disable (overriding defaults).
  - Parameter values for parameterised optimisations.
  - Human-readable description of intended use case.

Built-in profiles:
  - minimal:     Only essential optimizations, best for debugging.
  - default:     All stable optimizations enabled (sweet spot).
  - research:    All optimizations enabled (for novelty claims).
  - max:         All optimizations including experimental ones.
  - memory:      Optimize for minimal memory footprint.
  - debug:       All optimizations disabled, maximum instrumentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .registry import OptimizationRegistry


@dataclass
class OptimizationProfile:
    name: str
    description: str
    optimizations: dict[str, bool] = field(default_factory=dict)
    parameters: dict[str, dict[str, Any]] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    strict: bool = False

    def is_enabled(self, opt_name: str) -> bool | None:
        return self.optimizations.get(opt_name)


class ProfileManager:
    _profiles: dict[str, OptimizationProfile] = {}

    @classmethod
    def register(cls, profile: OptimizationProfile) -> None:
        cls._profiles[profile.name] = profile

    @classmethod
    def get(cls, name: str) -> OptimizationProfile | None:
        cls.initialize_defaults()
        return cls._profiles.get(name)

    @classmethod
    def all(cls) -> list[OptimizationProfile]:
        return list(cls._profiles.values())

    @classmethod
    def names(cls) -> list[str]:
        return list(cls._profiles.keys())

    @classmethod
    def initialize_defaults(cls) -> None:
        if cls._profiles:
            return

        # minimal — only what is needed for correctness
        cls.register(OptimizationProfile(
            name="minimal",
            description="Only essential optimizations for correctness",
            strict=True,
            optimizations={
                "sheaf.restriction_cache": True,
                "sheaf.global_section_cache": True,
                "query.constant_folding": True,
                "query.dead_operator_removal": True,
                "query.logical_simplification": True,
                "kg.dictionary_encoding": True,
                "kg.pragma_tuning": True,
            },
            tags=["debug", "correctness"],
        ))

        # default — stable optimizations, production sweet spot
        cls.register(OptimizationProfile(
            name="default",
            description="All stable optimizations enabled",
            optimizations={
                "sheaf.neighborhood_index": True,
                "sheaf.context_index": True,
                "sheaf.temporal_index": True,
                "sheaf.provenance_index": True,
                "sheaf.restriction_cache": True,
                "sheaf.global_section_cache": True,
                "query.lru_parsed_cache": True,
                "query.lru_logical_cache": True,
                "query.lru_physical_cache": True,
                "query.constant_folding": True,
                "query.predicate_pushdown": True,
                "query.projection_pushdown": True,
                "query.dead_operator_removal": True,
                "query.logical_simplification": True,
                "query.cost_optimizer": True,
                "kg.dictionary_encoding": True,
                "kg.dictionary_cache": True,
                "kg.join_reordering": True,
                "kg.filter_pushdown": True,
                "kg.batch_insert": True,
                "kg.pragma_tuning": True,
                "kg.reification_skip": True,
            },
            tags=["production", "stable"],
        ))

        # research — all non-experimental, for novelty claims
        cls.register(OptimizationProfile(
            name="research",
            description="All stable + research optimizations for paper claims",
            optimizations={
                "sheaf.neighborhood_index": True,
                "sheaf.context_index": True,
                "sheaf.temporal_index": True,
                "sheaf.provenance_index": True,
                "sheaf.restriction_cache": True,
                "sheaf.global_section_cache": True,
                "sheaf.section_dedup": True,
                "sheaf.context_aware_gluing": True,
                "query.lru_parsed_cache": True,
                "query.lru_logical_cache": True,
                "query.lru_physical_cache": True,
                "query.constant_folding": True,
                "query.predicate_pushdown": True,
                "query.projection_pushdown": True,
                "query.dead_operator_removal": True,
                "query.logical_simplification": True,
                "query.cost_optimizer": True,
                "query.result_caching": True,
                "kg.six_index": True,
                "kg.dictionary_encoding": True,
                "kg.dictionary_cache": True,
                "kg.join_reordering": True,
                "kg.filter_pushdown": True,
                "kg.batch_insert": True,
                "kg.pragma_tuning": True,
                "kg.reification_skip": True,
                "kg.result_caching": True,
            },
            tags=["paper", "novelty"],
        ))

        # max — everything, including experimental
        cls.register(OptimizationProfile(
            name="max",
            description="All optimizations enabled, including experimental",
            optimizations={e.name: True for e in OptimizationRegistry.all()},
            parameters={
                "sheaf.topology_compression": {"min_shared": 0.5},
                "sheaf.parallel_gluing": {"max_workers": 8},
            },
            tags=["experimental", "benchmark"],
        ))

        # memory — minimal memory footprint
        cls.register(OptimizationProfile(
            name="memory",
            description="Optimize for minimal memory usage",
            strict=True,
            optimizations={
                "sheaf.restriction_cache": True,
                "sheaf.global_section_cache": True,
                "sheaf.topology_compression": True,
                "sheaf.section_dedup": True,
                "sheaf.lazy_restriction": True,
                "kg.dictionary_encoding": True,
                "kg.reification_skip": True,
                "query.constant_folding": True,
                "query.dead_operator_removal": True,
                "query.logical_simplification": True,
            },
            parameters={
                "sheaf.topology_compression": {"min_shared": 0.9},
            },
            tags=["memory", "constrained"],
        ))

        # debug — all off, full instrumentation
        cls.register(OptimizationProfile(
            name="debug",
            description="All optimizations disabled for debugging",
            optimizations={e.name: False for e in OptimizationRegistry.all()},
            tags=["debug"],
        ))
