"""Visualization module for benchmark results and data structures.

Generates plots, tables, and diagrams used in the paper.
All figures are generated from benchmark output files,
ensuring every figure in the paper is reproducible.

Uses matplotlib for static plots and Rich for terminal output.
"""

from sfdb.visualization.plots import (
    BenchmarkPlotter,
    latency_comparison,
    memory_comparison,
    query_scaling,
    storage_comparison,
)

__all__ = [
    "BenchmarkPlotter",
    "latency_comparison",
    "memory_comparison",
    "query_scaling",
    "storage_comparison",
]
