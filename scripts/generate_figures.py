"""Generate benchmark figures for the SFDB paper.

Produces publication-quality PDF figures using matplotlib.
Uses a clean blue/orange categorical scheme (colorblind-safe).
"""

from __future__ import annotations

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

FIGS_DIR = Path(__file__).resolve().parent.parent / "paper" / "figures"
FIGS_DIR.mkdir(parents=True, exist_ok=True)

# Data
sizes = [100, 1000, 10000]
sizes_str = ["100", "1K", "10K"]

# LOOKUP latency (ms)
kg_lookup = [0.008, 0.520, 2.279]
sh_lookup = [0.003, 0.007, 0.074]

# GLOBAL latency (ms)
kg_global = [3.359, 3.718, 7.403]
sh_global = [3.244, 91.081, 10407.0]

# Insert latency (ms)
kg_insert = [5.8, 59.0, 651.1]
sh_insert = [5.1, 54.1, 627.0]


def save(fig: plt.Figure, name: str) -> None:
    path = FIGS_DIR / name
    fig.savefig(str(path), bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved {path}")


def latency_chart() -> None:
    """Latency comparison: KG vs Sheaf for LOOKUP and GLOBAL."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4), sharey=False)

    x = np.arange(len(sizes))
    w = 0.35

    # LOOKUP subplot
    ax1.bar(x - w / 2, kg_lookup, w, label="KG", color=KG_COLOR, edgecolor="white", linewidth=0.5)
    ax1.bar(x + w / 2, sh_lookup, w, label="SheafDB", color=SHEAF_COLOR, edgecolor="white", linewidth=0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(sizes_str)
    ax1.set_xlabel("Dataset size (facts)")
    ax1.set_ylabel("Latency (ms)")
    ax1.set_title("LOOKUP Query")
    ax1.legend(fontsize=8)
    ax1.set_yscale("log")
    ax1.grid(axis="y", alpha=0.3, linestyle=":")

    # GLOBAL subplot
    ax2.bar(x - w / 2, kg_global, w, label="KG", color=KG_COLOR, edgecolor="white", linewidth=0.5)
    ax2.bar(x + w / 2, sh_global, w, label="SheafDB", color=SHEAF_COLOR, edgecolor="white", linewidth=0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(sizes_str)
    ax2.set_xlabel("Dataset size (facts)")
    ax2.set_ylabel("Latency (ms)")
    ax2.set_title("GLOBAL Query")
    ax2.legend(fontsize=8)
    ax2.set_yscale("log")
    ax2.grid(axis="y", alpha=0.3, linestyle=":")

    fig.suptitle("Query Latency: KG vs SheafDB", fontsize=12, y=1.02)
    fig.tight_layout()
    save(fig, "latency.pdf")


def throughput_chart() -> None:
    """Insert throughput comparison."""
    fig, ax = plt.subplots(figsize=(6, 4))

    x = np.arange(len(sizes))
    w = 0.35

    ax.bar(x - w / 2, kg_insert, w, label="KG", color=KG_COLOR, edgecolor="white", linewidth=0.5)
    ax.bar(x + w / 2, sh_insert, w, label="SheafDB", color=SHEAF_COLOR, edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(sizes_str)
    ax.set_xlabel("Dataset size (facts)")
    ax.set_ylabel("Insert time (ms)")
    ax.set_title("Insert Throughput")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle=":")

    # Annotate ratio
    for i in range(len(sizes)):
        ratio = sh_insert[i] / kg_insert[i]
        mid = (kg_insert[i] + sh_insert[i]) / 2
        ax.annotate(f"{ratio:.2f}x", (x[i], mid), ha="center", va="bottom", fontsize=8, fontweight="bold")

    fig.tight_layout()
    save(fig, "throughput.pdf")


def speedup_chart() -> None:
    """Speedup ratio: Sheaf / KG. Below 1 = Sheaf faster, above 1 = KG faster."""
    fig, ax = plt.subplots(figsize=(6, 4))

    lookup_ratio = [s / k for s, k in zip(sh_lookup, kg_lookup)]
    global_ratio = [s / k for s, k in zip(sh_global, kg_global)]

    x = np.arange(len(sizes))
    w = 0.35

    ax.bar(x - w / 2, lookup_ratio, w, label="LOOKUP", color=KG_COLOR, edgecolor="white", linewidth=0.5)
    ax.bar(x + w / 2, global_ratio, w, label="GLOBAL", color=SHEAF_COLOR, edgecolor="white", linewidth=0.5)
    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=0.8, label="Parity")

    ax.set_xticks(x)
    ax.set_xticklabels(sizes_str)
    ax.set_xlabel("Dataset size (facts)")
    ax.set_ylabel("SheafDB / KG ratio")
    ax.set_title("Speedup Ratio (below 1 = SheafDB faster)")
    ax.legend(fontsize=9)
    ax.set_yscale("log")
    ax.grid(axis="y", alpha=0.3, linestyle=":")

    # Annotate values
    for i in range(len(sizes)):
        ax.annotate(f"{lookup_ratio[i]:.2f}x", (x[i] - w / 2, lookup_ratio[i]), ha="center", va="bottom" if lookup_ratio[i] < 1 else "top", fontsize=7)
        ax.annotate(f"{global_ratio[i]:.1f}x", (x[i] + w / 2, global_ratio[i]), ha="center", va="bottom" if global_ratio[i] < 1 else "top", fontsize=7)

    fig.tight_layout()
    save(fig, "speedup.pdf")


def scalability_chart() -> None:
    """Scalability: latency vs dataset size for both engines."""
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.plot(sizes, kg_lookup, "o-", color=KG_COLOR, label="KG LOOKUP", linewidth=1.5, markersize=6)
    ax.plot(sizes, sh_lookup, "s-", color=SHEAF_COLOR, label="SheafDB LOOKUP", linewidth=1.5, markersize=6)
    ax.plot(sizes, kg_global, "o--", color=KG_COLOR_LIGHT, label="KG GLOBAL", linewidth=1.5, markersize=6)
    ax.plot(sizes, sh_global, "s--", color=SHEAF_COLOR_LIGHT, label="SheafDB GLOBAL", linewidth=1.5, markersize=6)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(sizes)
    ax.set_xticklabels(sizes_str)
    ax.set_xlabel("Dataset size (facts)")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Scalability: Latency vs Dataset Size")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, linestyle=":")

    fig.tight_layout()
    save(fig, "scalability.pdf")


def main() -> None:
    print("Generating figures...")
    latency_chart()
    throughput_chart()
    speedup_chart()
    scalability_chart()
    print("Done.")


if __name__ == "__main__":
    main()
