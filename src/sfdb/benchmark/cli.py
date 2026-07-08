"""Benchmark CLI commands."""

from __future__ import annotations

import argparse
import logging
import sys

from sfdb.benchmark.config import BenchmarkConfig, BenchmarkMode, CacheMode, DatasetSize
from sfdb.benchmark.runner import BenchmarkRunner
from sfdb.benchmark.visualization import VisualizationEngine
from sfdb.datasets.synthetic import SyntheticConfig, generate_facts


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Semantic Fact DB Benchmark Suite")
    sub = p.add_subparsers(dest="command", required=True)

    p_benchmark = sub.add_parser("benchmark", help="Run a benchmark")
    p_benchmark.add_argument("--name", default="benchmark", help="Benchmark name")
    p_benchmark.add_argument(
        "--size", choices=["tiny", "small", "medium", "large", "very_large"], default="small"
    )
    p_benchmark.add_argument(
        "--mode",
        choices=[
            "micro",
            "macro",
            "stress",
            "scalability",
            "consistency",
            "storage",
            "import",
            "export",
        ],
        default="micro",
    )
    p_benchmark.add_argument("--cache", choices=["cold", "warm"], default="cold")
    p_benchmark.add_argument("--runs-cold", type=int, default=10)
    p_benchmark.add_argument("--runs-warm", type=int, default=50)
    p_benchmark.add_argument("--seed", type=int, default=42)
    p_benchmark.add_argument("--engines", nargs="+", default=["KnowledgeGraph", "SheafDatabase"])
    p_benchmark.add_argument(
        "--queries",
        nargs="+",
        default=["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"],
    )
    p_benchmark.add_argument("--output-dir", default="results")
    p_benchmark.add_argument("--no-visualize", action="store_true")
    p_benchmark.add_argument("--num-facts", type=int, default=1000)
    p_benchmark.add_argument("--num-entities", type=int, default=100)

    p_all = sub.add_parser("benchmark-all", help="Run all benchmarks")
    p_query = sub.add_parser("benchmark-query", help="Run a single query benchmark")
    p_query.add_argument("query_id", help="Query ID (Q1-Q15)")
    p_storage = sub.add_parser("benchmark-storage", help="Run storage benchmark")
    p_import = sub.add_parser("benchmark-import", help="Run import benchmark")
    p_consistency = sub.add_parser("benchmark-consistency", help="Run consistency benchmark")
    p_scalability = sub.add_parser("benchmark-scalability", help="Run scalability benchmark")

    for cp in [p_all, p_query, p_storage, p_import, p_consistency, p_scalability]:
        cp.add_argument("--name", default="benchmark")
        cp.add_argument("--seed", type=int, default=42)
        cp.add_argument("--output-dir", default="results")

    return p


def _size_to_facts(size: str) -> int:
    return {
        "tiny": 100,
        "small": 1000,
        "medium": 10000,
        "large": 100000,
        "very_large": 1000000,
    }.get(size, 1000)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "benchmark":
        num_facts = getattr(args, "num_facts", None) or _size_to_facts(args.size)
        num_entities = getattr(args, "num_entities", 100)
        ds = generate_facts(
            SyntheticConfig(num_facts=num_facts, num_entities=num_entities, seed=args.seed)
        )
        config = BenchmarkConfig(
            name=args.name,
            dataset_size=DatasetSize[args.size.upper()],
            mode=BenchmarkMode[args.mode.upper()],
            cache=CacheMode[args.cache.upper()],
            num_runs_cold=args.runs_cold,
            num_runs_warm=args.runs_warm,
            seed=args.seed,
            output_dir=args.output_dir,
            engines=tuple(args.engines),
            queries=tuple(args.queries),
            visualize=not args.no_visualize,
        )
        runner = BenchmarkRunner(config)
        runner.initialize(ds.facts)
        result = runner.run()
        logging.info("Verification: %s", result.verification.message)
        if not args.no_visualize:
            viz = VisualizationEngine(output_dir=f"{args.output_dir}/figures")
            lat_data: dict[str, dict[str, list[float]]] = {}
            for en, qs in result.engine_results.items():
                lat_data[en] = {
                    qid: [m.latency_ms for m in metrics] for qid, metrics in qs.items()
                }
            viz.latency_plot(lat_data, f"{args.name}_latency")
            logging.info("Figures saved to %s/figures", args.output_dir)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
