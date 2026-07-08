#!/usr/bin/env python3
"""CLI entry point for running benchmarks.

Usage:
    uv run python scripts/run_benchmarks.py --dataset-size 100 500 1000
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from sfdb.benchmark.runner import BenchmarkConfig, BenchmarkRunner
from sfdb.common.types import Identifier
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts
from sfdb.query.language import Query, QueryPattern, QueryType
from sfdb.utils.logging import setup_logging

app = typer.Typer()
setup_logging()


def make_point_query(subject_str: str) -> Query:
    """Create a point lookup query."""
    return Query(
        type=QueryType.FACT,
        pattern=QueryPattern(
            subject=Identifier(subject_str),
        ),
    )


def make_walk_query(start_str: str, relation_str: str) -> Query:
    """Create a walk traversal query."""
    return Query(
        type=QueryType.WALK,
        start=Identifier(start_str),
        relation=Identifier(relation_str),
        max_depth=2,
    )


@app.command()
def run(
    dataset_size: list[int] = typer.Option([100, 500], help="Dataset sizes to test"),
    num_runs: int = typer.Option(3, help="Number of benchmark runs"),
    output: str = typer.Option("results/benchmark.json", help="Output path"),
) -> None:
    """Run the full benchmark suite."""
    results = []
    for size in dataset_size:
        # Generate dataset
        config = SyntheticConfig(num_entities=size // 2, num_facts=size, seed=42)
        dataset = generate_facts(config)

        # Create queries
        queries = [
            make_point_query(f"entity_{(size // 4)}"),
            make_walk_query(f"entity_{0}", "relation_0"),
        ]

        # Create benchmark config
        bench_config = BenchmarkConfig(
            name=f"size_{size}",
            queries=tuple(queries),
            num_runs=num_runs,
            seed=42,
            output_dir="results",
        )

        # Run
        runner = BenchmarkRunner(bench_config)
        runner.initialize(dataset.facts)
        result = runner.run()
        results.append(result.to_dict())

    # Save consolidated results
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2))
    typer.echo(f"Results saved to {output_path}")


@app.command()
def generate_plots(results_path: str = "results/benchmark.json") -> None:
    """Generate plots from benchmark results."""
    from sfdb.visualization.plots import (
        latency_comparison,
        memory_comparison,
        query_scaling,
        storage_comparison,
    )

    results = json.loads(Path(results_path).read_text())
    latency_comparison(results)
    memory_comparison(results)
    storage_comparison(results)
    query_scaling(results)
    typer.echo("Plots generated in paper/figures/")


if __name__ == "__main__":
    app()
