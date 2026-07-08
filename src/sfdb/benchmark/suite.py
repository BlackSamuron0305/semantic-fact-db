"""Benchmark suite: groups related benchmarks with shared configuration.

A BenchmarkSuite is a collection of BenchmarkRunners that share a
common dataset and produce a unified report.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sfdb.benchmark.runner import BenchmarkConfig, BenchmarkResult, BenchmarkRunner
from sfdb.common.types import Fact


@dataclass(slots=True)
class BenchmarkSuite:
    """A suite of related benchmarks.

    Parameters
    ----------
    name: Name of the suite.
    output_dir: Directory for results.
    """

    name: str = "default"
    output_dir: str = "results"

    def run_all(
        self, configs: list[BenchmarkConfig], datasets: list[list[Fact]]
    ) -> list[BenchmarkResult]:
        """Run all benchmark configurations."""
        results: list[BenchmarkResult] = []
        for config, facts in zip(configs, datasets, strict=True):
            runner = BenchmarkRunner(config)
            runner.initialize(facts)
            result = runner.run()
            result.save(Path(self.output_dir) / f"{config.name}.json")
            results.append(result)
        return results
