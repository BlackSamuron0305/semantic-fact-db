"""Visualization functions for benchmark results.

All plot functions accept benchmark result files or data dicts
and produce matplotlib figures. This ensures reproducibility:
the paper's figures are always generated from actual benchmark output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")


class BenchmarkPlotter:
    """Generates publication-quality plots from benchmark results."""

    def __init__(self, output_dir: str = "paper/figures") -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def latency_comparison(
        self, results: list[dict[str, Any]], filename: str = "latency.pdf"
    ) -> Path:
        """Plot latency comparison: KG vs Sheaf across query types."""
        fig, ax = plt.subplots(figsize=(8, 5))
        labels = [r.get("config", {}).get("name", "unknown") for r in results]
        kg_latencies = [r.get("kg", {}).get("avg_latency_ms", 0) for r in results]
        sheaf_latencies = [r.get("sheaf", {}).get("avg_latency_ms", 0) for r in results]

        x = np.arange(len(labels))
        width = 0.35

        ax.bar(x - width / 2, kg_latencies, width, label="KG", color="#4C72B0")
        ax.bar(x + width / 2, sheaf_latencies, width, label="SheafDB", color="#DD8452")

        ax.set_xlabel("Query Type")
        ax.set_ylabel("Latency (ms)")
        ax.set_title("Query Latency: KG vs SheafDB")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        path = self._output_dir / filename
        fig.savefig(str(path), bbox_inches="tight")
        plt.close(fig)
        return path

    def memory_comparison(
        self, results: list[dict[str, Any]], filename: str = "memory.pdf"
    ) -> Path:
        """Plot memory usage comparison."""
        fig, ax = plt.subplots(figsize=(8, 5))
        labels = [r.get("config", {}).get("name", "unknown") for r in results]
        kg_memory = [r.get("kg", {}).get("avg_memory_mb", 0) for r in results]
        sheaf_memory = [r.get("sheaf", {}).get("avg_memory_mb", 0) for r in results]

        x = np.arange(len(labels))
        width = 0.35

        ax.bar(x - width / 2, kg_memory, width, label="KG", color="#4C72B0")
        ax.bar(x + width / 2, sheaf_memory, width, label="SheafDB", color="#DD8452")

        ax.set_xlabel("Query Type")
        ax.set_ylabel("Memory (MB)")
        ax.set_title("Memory Usage: KG vs SheafDB")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        path = self._output_dir / filename
        fig.savefig(str(path), bbox_inches="tight")
        plt.close(fig)
        return path


def latency_comparison(results: list[dict[str, Any]], output_dir: str = "paper/figures") -> Path:
    """Convenience function for latency comparison plot."""
    plotter = BenchmarkPlotter(output_dir)
    return plotter.latency_comparison(results)


def memory_comparison(results: list[dict[str, Any]], output_dir: str = "paper/figures") -> Path:
    """Convenience function for memory comparison plot."""
    plotter = BenchmarkPlotter(output_dir)
    return plotter.memory_comparison(results)


def storage_comparison(results: list[dict[str, Any]], output_dir: str = "paper/figures") -> Path:
    """Convenience function for storage comparison plot."""
    plotter = BenchmarkPlotter(output_dir)
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = [r.get("config", {}).get("name", "unknown") for r in results]
    kg_storage = [r.get("kg", {}).get("storage_bytes", 0) / 1024 for r in results]
    sheaf_storage = [r.get("sheaf", {}).get("storage_bytes", 0) / 1024 for r in results]

    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width / 2, kg_storage, width, label="KG", color="#4C72B0")
    ax.bar(x + width / 2, sheaf_storage, width, label="SheafDB", color="#DD8452")
    ax.set_xlabel("Dataset")
    ax.set_ylabel("Storage (KB)")
    ax.set_title("Storage Overhead: KG vs SheafDB")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = plotter._output_dir / "storage.pdf"
    fig.savefig(str(path), bbox_inches="tight")
    plt.close(fig)
    return path


def query_scaling(results: list[dict[str, Any]], output_dir: str = "paper/figures") -> Path:
    """Convenience function for query scaling plot."""
    plotter = BenchmarkPlotter(output_dir)
    fig, ax = plt.subplots(figsize=(8, 5))
    sizes = [r.get("config", {}).get("num_facts", 0) for r in results]
    kg_times = [r.get("kg", {}).get("avg_latency_ms", 0) for r in results]
    sheaf_times = [r.get("sheaf", {}).get("avg_latency_ms", 0) for r in results]

    ax.plot(sizes, kg_times, "o-", label="KG", color="#4C72B0")
    ax.plot(sizes, sheaf_times, "s-", label="SheafDB", color="#DD8452")
    ax.set_xlabel("Dataset Size (facts)")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Query Scaling: Latency vs Dataset Size")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = plotter._output_dir / "scaling.pdf"
    fig.savefig(str(path), bbox_inches="tight")
    plt.close(fig)
    return path
