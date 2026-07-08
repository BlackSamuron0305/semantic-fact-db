"""Publication-quality visualization — plots, charts, figures."""

from __future__ import annotations

from pathlib import Path


class VisualizationEngine:
    def __init__(self, output_dir: str = "results/figures") -> None:
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._matplotlib = False
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            self._plt = plt
            self._matplotlib = True
        except ImportError:
            pass

    def latency_plot(
        self, data: dict[str, dict[str, list[float]]], name: str = "latency"
    ) -> list[str]:
        if not self._matplotlib or not data:
            return []
        import numpy as np

        _fig, ax = self._plt.subplots(figsize=(10, 6))
        for engine, queries in data.items():
            means = [np.mean(v) for v in queries.values()]
            ax.plot(list(queries.keys()), means, marker="o", label=engine)
        ax.set_xlabel("Query")
        ax.set_ylabel("Latency (ms)")
        ax.set_title("Query Latency Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        return self._save(name)

    def throughput_plot(
        self, data: dict[str, dict[str, list[float]]], name: str = "throughput"
    ) -> list[str]:
        if not self._matplotlib:
            return []
        import numpy as np

        _fig, ax = self._plt.subplots(figsize=(10, 6))
        for engine, queries in data.items():
            throughput = [
                1.0 / (np.mean(v) / 1000) if np.mean(v) > 0 else 0 for v in queries.values()
            ]
            ax.bar(list(queries.keys()), throughput, alpha=0.7, label=engine)
        ax.set_xlabel("Query")
        ax.set_ylabel("Throughput (queries/sec)")
        ax.set_title("Query Throughput Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        return self._save(name)

    def memory_plot(
        self, data: dict[str, dict[str, list[float]]], name: str = "memory"
    ) -> list[str]:
        if not self._matplotlib:
            return []
        import numpy as np

        _fig, ax = self._plt.subplots(figsize=(10, 6))
        for engine, queries in data.items():
            mems = [np.mean(v) / 1e6 for v in queries.values()]
            ax.plot(list(queries.keys()), mems, marker="s", label=engine)
        ax.set_xlabel("Query")
        ax.set_ylabel("Memory (MB)")
        ax.set_title("Memory Usage Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        return self._save(name)

    def scalability_plot(
        self, data: dict[str, dict[str, list[float]]], name: str = "scalability"
    ) -> list[str]:
        if not self._matplotlib:
            return []
        import numpy as np

        _fig, ax = self._plt.subplots(figsize=(10, 6))
        for engine, sizes in data.items():
            xs = [int(k.split("_")[1]) if "_" in k else len(list(sizes.keys())) for k in sizes]
            ys = [np.mean(v) for v in sizes.values()]
            ax.plot(xs, ys, marker="^", label=engine)
        ax.set_xlabel("Dataset Size (facts)")
        ax.set_ylabel("Latency (ms)")
        ax.set_title("Scalability Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        return self._save(name)

    def speedup_plot(
        self, baseline: str, data: dict[str, dict[str, float]], name: str = "speedup"
    ) -> list[str]:
        if not self._matplotlib:
            return []
        _fig, ax = self._plt.subplots(figsize=(10, 6))
        for engine, speedups in data.items():
            if engine == baseline:
                continue
            ax.plot(
                list(speedups.keys()),
                list(speedups.values()),
                marker="D",
                label=f"{engine} vs {baseline}",
            )
        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlabel("Query")
        ax.set_ylabel("Speedup Ratio")
        ax.set_title("Speedup Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        return self._save(name)

    def radar_chart(self, data: dict[str, dict[str, float]], name: str = "radar") -> list[str]:
        if not self._matplotlib:
            return []
        import numpy as np

        categories = list(next(iter(data.values())).keys())
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        _fig, ax = self._plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})
        for engine, values in data.items():
            vals = list(values.values())
            vals += vals[:1]
            ax.plot(angles, vals, "o-", linewidth=2, label=engine)
            ax.fill(angles, vals, alpha=0.1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=8)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))
        ax.set_title("Benchmark Radar Comparison", size=14)
        return self._save(name)

    def cdf_plot(self, data: dict[str, list[float]], name: str = "cdf") -> list[str]:
        if not self._matplotlib:
            return []
        import numpy as np

        _fig, ax = self._plt.subplots(figsize=(10, 6))
        for label, values in data.items():
            sorted_vals = np.sort(values)
            y = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
            ax.plot(sorted_vals, y, label=label)
        ax.set_xlabel("Latency (ms)")
        ax.set_ylabel("CDF")
        ax.set_title("Cumulative Distribution of Latency")
        ax.legend()
        ax.grid(True, alpha=0.3)
        return self._save(name)

    def box_plot(self, data: dict[str, list[float]], name: str = "box") -> list[str]:
        if not self._matplotlib:
            return []
        _fig, ax = self._plt.subplots(figsize=(10, 6))
        labels = list(data.keys())
        values = list(data.values())
        bp = ax.boxplot(values, labels=labels, patch_artist=True)
        for box in bp["boxes"]:
            box.set_alpha(0.6)
        ax.set_xlabel("Engine")
        ax.set_ylabel("Latency (ms)")
        ax.set_title("Latency Distribution")
        ax.grid(True, alpha=0.3)
        self._plt.setp(bp["labels"], rotation=45)
        self._plt.tight_layout()
        return self._save(name)

    def heatmap(self, data: dict[str, dict[str, float]], name: str = "heatmap") -> list[str]:
        if not self._matplotlib:
            return []
        import numpy as np

        engines = list(data.keys())
        queries = list(data[engines[0]].keys())
        vals = np.array([[data[e][q] for q in queries] for e in engines])
        _fig, ax = self._plt.subplots(figsize=(10, 6))
        im = ax.imshow(vals, cmap="YlOrRd", aspect="auto")
        self._plt.colorbar(im, label="Latency (ms)")
        ax.set_xticks(range(len(queries)))
        ax.set_yticks(range(len(engines)))
        ax.set_xticklabels(queries, rotation=45, ha="right")
        ax.set_yticklabels(engines)
        ax.set_title("Latency Heatmap")
        for i in range(len(engines)):
            for j in range(len(queries)):
                ax.text(
                    j, i, f"{vals[i, j]:.1f}", ha="center", va="center", color="black", fontsize=8
                )
        self._plt.tight_layout()
        return self._save(name)

    def _save(self, name: str) -> list[str]:
        paths: list[str] = []
        for ext in ("pdf", "svg", "png"):
            p = str(self._dir / f"{name}.{ext}")
            self._plt.savefig(p, dpi=300, bbox_inches="tight")
            paths.append(p)
        self._plt.close()
        return paths
