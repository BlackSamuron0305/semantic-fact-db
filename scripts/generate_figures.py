"""Generate benchmark figures for the SFDB paper from real results.

Reads results/paper_suite_summary.json (produced by `uv run sfdb
benchmark`) and produces publication-quality PDF figures with matplotlib.
Uses a clean blue/orange categorical scheme (colorblind-safe). Run
scripts/generate_tables.py's sibling `uv run sfdb benchmark` first if the
summary file does not exist or is stale.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

# Colorblind-safe palette: blue (#4C72B0) and orange (#DD8452)
KG_COLOR = "#4C72B0"
SHEAF_COLOR = "#DD8452"
KG_COLOR_LIGHT = "#8DB0D8"
SHEAF_COLOR_LIGHT = "#E8B97A"

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGS_DIR = REPO_ROOT / "paper" / "figures"
FIGS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = REPO_ROOT / "results" / "paper_suite_summary.json"

QUERY_CLASSES = ("LOOKUP", "GLOBAL", "TEMPORAL", "TEMPORAL_UNBOUNDED")
QUERY_CLASS_TITLES = {
    "LOOKUP": "LOOKUP",
    "GLOBAL": "GLOBAL",
    "TEMPORAL": "TEMPORAL (bounded)",
    "TEMPORAL_UNBOUNDED": "TEMPORAL (unbounded)",
}


def load_summary() -> dict:
    if not SUMMARY_PATH.exists():
        print(f"error: {SUMMARY_PATH} not found. Run `uv run sfdb benchmark` first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(SUMMARY_PATH.read_text())


def sizes_from(summary: dict) -> list[int]:
    return sorted(int(n) for n in summary["query"])


def size_labels(sizes: list[int]) -> list[str]:
    return [f"{n // 1000}K" if n >= 1000 else str(n) for n in sizes]


def means(summary: dict, qclass: str, sizes: list[int]) -> tuple[list[float], list[float]]:
    kg = [summary["query"][str(n)][qclass]["stats"]["KnowledgeGraph"]["mean"] for n in sizes]
    sh = [summary["query"][str(n)][qclass]["stats"]["SheafDatabase"]["mean"] for n in sizes]
    return kg, sh


def insert_means(summary: dict, sizes: list[int]) -> tuple[list[float], list[float]]:
    kg = [summary["insert"][str(n)]["KnowledgeGraph"]["mean"] for n in sizes]
    sh = [summary["insert"][str(n)]["SheafDatabase"]["mean"] for n in sizes]
    return kg, sh


def memory_means_mb(summary: dict, sizes: list[int]) -> tuple[list[float], list[float]]:
    mem = summary.get("insert_memory_bytes", {})
    kg = [mem.get(str(n), {}).get("KnowledgeGraph", 0.0) / 1e6 for n in sizes]
    sh = [mem.get(str(n), {}).get("SheafDatabase", 0.0) / 1e6 for n in sizes]
    return kg, sh


def save(fig: plt.Figure, name: str) -> None:
    path = FIGS_DIR / name
    fig.savefig(str(path), bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved {path}")


def latency_chart(summary: dict, sizes: list[int], labels: list[str]) -> None:
    """Latency comparison: KG vs SFDB for LOOKUP, GLOBAL, TEMPORAL (bounded and unbounded)."""
    fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=False)
    x = np.arange(len(sizes))
    w = 0.35

    for ax, qclass in zip(axes, QUERY_CLASSES):
        kg, sh = means(summary, qclass, sizes)
        ax.bar(x - w / 2, kg, w, label="KG", color=KG_COLOR, edgecolor="white", linewidth=0.5)
        ax.bar(x + w / 2, sh, w, label="SheafDB", color=SHEAF_COLOR, edgecolor="white", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_xlabel("Dataset size (facts)")
        ax.set_ylabel("Latency (ms)")
        ax.set_title(f"{QUERY_CLASS_TITLES[qclass]} Query")
        ax.legend(fontsize=8)
        ax.set_yscale("log")
        ax.grid(axis="y", alpha=0.3, linestyle=":")

    fig.suptitle("Query Latency: KG vs SheafDB", fontsize=12, y=1.02)
    fig.tight_layout()
    save(fig, "latency.pdf")


def throughput_chart(summary: dict, sizes: list[int], labels: list[str]) -> None:
    """Insert throughput comparison."""
    fig, ax = plt.subplots(figsize=(6, 4))
    kg, sh = insert_means(summary, sizes)
    x = np.arange(len(sizes))
    w = 0.35

    ax.bar(x - w / 2, kg, w, label="KG", color=KG_COLOR, edgecolor="white", linewidth=0.5)
    ax.bar(x + w / 2, sh, w, label="SheafDB", color=SHEAF_COLOR, edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Dataset size (facts)")
    ax.set_ylabel("Insert time (ms)")
    ax.set_title("Insert Throughput")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle=":")

    for i in range(len(sizes)):
        ratio = sh[i] / kg[i] if kg[i] else float("nan")
        mid = (kg[i] + sh[i]) / 2
        ax.annotate(f"{ratio:.2f}x", (x[i], mid), ha="center", va="bottom", fontsize=8, fontweight="bold")

    fig.tight_layout()
    save(fig, "throughput.pdf")


def speedup_chart(summary: dict, sizes: list[int], labels: list[str]) -> None:
    """Speedup ratio: SFDB / KG per query class. Below 1 = SFDB faster."""
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(sizes))
    w = 0.2
    colors = [KG_COLOR, SHEAF_COLOR, "#55A868", "#8C564B"]

    for i, qclass in enumerate(QUERY_CLASSES):
        kg, sh = means(summary, qclass, sizes)
        ratio = [s / k if k else float("nan") for s, k in zip(sh, kg)]
        offset = (i - 1.5) * w
        ax.bar(x + offset, ratio, w, label=QUERY_CLASS_TITLES[qclass], color=colors[i], edgecolor="white", linewidth=0.5)
        for xi, r in zip(x, ratio):
            ax.annotate(f"{r:.2f}x", (xi + offset, r), ha="center",
                        va="bottom" if r < 1 else "top", fontsize=6)

    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=0.8, label="Parity")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Dataset size (facts)")
    ax.set_ylabel("SheafDB / KG latency ratio")
    ax.set_title("Speedup Ratio by Query Class (below 1 = SheafDB faster)")
    ax.legend(fontsize=8)
    ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.3, linestyle=":")

    fig.tight_layout()
    save(fig, "speedup.pdf")


def scalability_chart(summary: dict, sizes: list[int], labels: list[str]) -> None:
    """Scalability: latency vs dataset size for both engines, all classes."""
    fig, ax = plt.subplots(figsize=(7, 5))
    markers = {"LOOKUP": "s", "GLOBAL": "^", "TEMPORAL": "d", "TEMPORAL_UNBOUNDED": "o"}

    for qclass in QUERY_CLASSES:
        kg, sh = means(summary, qclass, sizes)
        label = QUERY_CLASS_TITLES[qclass]
        ax.plot(sizes, kg, marker=markers[qclass], linestyle="-", color=KG_COLOR,
                label=f"KG {label}", linewidth=1.3, markersize=6, alpha=0.9)
        ax.plot(sizes, sh, marker=markers[qclass], linestyle="--", color=SHEAF_COLOR,
                label=f"SheafDB {label}", linewidth=1.3, markersize=6, alpha=0.9)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(sizes)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Dataset size (facts)")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Scalability: Latency vs Dataset Size")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3, linestyle=":")

    fig.tight_layout()
    save(fig, "scalability.pdf")


def memory_chart(summary: dict, sizes: list[int], labels: list[str]) -> None:
    """Resident memory delta from inserting N facts."""
    fig, ax = plt.subplots(figsize=(6, 4))
    kg, sh = memory_means_mb(summary, sizes)
    x = np.arange(len(sizes))
    w = 0.35

    ax.bar(x - w / 2, kg, w, label="KG", color=KG_COLOR, edgecolor="white", linewidth=0.5)
    ax.bar(x + w / 2, sh, w, label="SheafDB", color=SHEAF_COLOR, edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Dataset size (facts)")
    ax.set_ylabel("Resident memory delta (MB)")
    ax.set_title("Memory Footprint: KG vs SheafDB")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle=":")

    for i in range(len(sizes)):
        ratio = sh[i] / kg[i] if kg[i] else float("nan")
        mid = max(kg[i], sh[i])
        ax.annotate(f"{ratio:.2f}x", (x[i], mid), ha="center", va="bottom", fontsize=8, fontweight="bold")

    fig.tight_layout()
    save(fig, "memory.pdf")


def main() -> None:
    print("Loading results/paper_suite_summary.json...")
    summary = load_summary()
    sizes = sizes_from(summary)
    labels = size_labels(sizes)

    print("Generating figures...")
    latency_chart(summary, sizes, labels)
    throughput_chart(summary, sizes, labels)
    speedup_chart(summary, sizes, labels)
    scalability_chart(summary, sizes, labels)
    memory_chart(summary, sizes, labels)
    print("Done.")


if __name__ == "__main__":
    main()
