"""Benchmark configuration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class DatasetSize(Enum):
    TINY = auto()
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    VERY_LARGE = auto()


class BenchmarkMode(Enum):
    MICRO = auto()
    MACRO = auto()
    STRESS = auto()
    SCALABILITY = auto()
    CONSISTENCY = auto()
    STORAGE = auto()
    IMPORT = auto()
    EXPORT = auto()


class CacheMode(Enum):
    COLD = auto()
    WARM = auto()


@dataclass(slots=True, frozen=True)
class BenchmarkConfig:
    name: str = "benchmark"
    dataset_size: DatasetSize = DatasetSize.SMALL
    mode: BenchmarkMode = BenchmarkMode.MICRO
    cache: CacheMode = CacheMode.COLD
    num_runs_cold: int = 10
    num_runs_warm: int = 50
    warm_up: int = 2
    seed: int = 42
    output_dir: str = "results"
    dataset_path: str = ""
    engines: tuple[str, ...] = ("KnowledgeGraph", "SheafDatabase")
    queries: tuple[str, ...] = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10")
    profile: bool = True
    visualize: bool = True
    export_latex: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dataset_size": self.dataset_size.name,
            "mode": self.mode.name,
            "cache": self.cache.name,
            "num_runs_cold": self.num_runs_cold,
            "num_runs_warm": self.num_runs_warm,
            "seed": self.seed,
            "engines": list(self.engines),
            "queries": list(self.queries),
        }
