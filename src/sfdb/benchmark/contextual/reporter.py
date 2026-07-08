"""Result reporting for contextual benchmarks — tables, plots, LaTeX."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from sfdb.benchmark.contextual.benchmarks import ContextualBenchResult
from sfdb.benchmark.contextual.metrics import ContextualMetrics
from sfdb.benchmark.statistics import Statistics, compute_statistics


@dataclass
class ContextualBenchReporter:
    results: list[ContextualBenchResult] = field(default_factory=list)

    def add(self, result: ContextualBenchResult) -> None:
        self.results.append(result)

    def merge(self, results: list[ContextualBenchResult]) -> None:
        self.results.extend(results)

    def latency_table(self) -> dict[str, dict[str, float]]:
        table: dict[str, dict[str, float]] = {}
        for r in self.results:
            table.setdefault(r.engine, {})[r.workload_id] = r.metrics.latency_ms
        return table

    def result_count_table(self) -> dict[str, dict[str, int]]:
        table: dict[str, dict[str, int]] = {}
        for r in self.results:
            table.setdefault(r.engine, {})[r.workload_id] = r.metrics.result_count
        return table

    def speedup_table(self, baseline_engine: str = "KnowledgeGraph") -> dict[str, dict[str, float]]:
        lt = self.latency_table()
        baseline = lt.get(baseline_engine, {})
        speedups: dict[str, dict[str, float]] = {}
        for engine, workloads in lt.items():
            if engine == baseline_engine:
                continue
            speedups[engine] = {}
            for wid, lat in workloads.items():
                bl = baseline.get(wid, 0.0)
                speedups[engine][wid] = bl / lat if lat > 0 else float("inf")
        return speedups

    def summary_stats(self) -> dict[str, dict[str, Statistics]]:
        by_engine: dict[str, dict[str, list[float]]] = {}
        for r in self.results:
            by_engine.setdefault(r.engine, {}).setdefault(r.workload_id, []).append(r.metrics.latency_ms)
        stats: dict[str, dict[str, Statistics]] = {}
        for engine, workloads in by_engine.items():
            stats[engine] = {}
            for wid, vals in workloads.items():
                stats[engine][wid] = compute_statistics(vals)
        return stats

    def to_markdown(self) -> str:
        lines = ["# Contextual Benchmark Results\n"]
        lines.append("## Latency (ms)\n")
        lines.append("| Workload | KnowledgeGraph | SheafDatabase | Speedup |")
        lines.append("|---|---|---|---|")
        lt = self.latency_table()
        st = self.speedup_table()
        all_wids = sorted({wid for e in lt.values() for wid in e})
        for wid in all_wids:
            kg = lt.get("KnowledgeGraph", {}).get(wid, float("nan"))
            sheaf = lt.get("SheafDatabase", {}).get(wid, float("nan"))
            speedup = sheaf / kg if kg and sheaf else float("nan")
            kg_s = f"{kg:.2f}" if not math.isnan(kg) else "—"
            sheaf_s = f"{sheaf:.2f}" if not math.isnan(sheaf) else "—"
            speedup_s = f"{speedup:.2f}x" if not math.isnan(speedup) else "—"
            lines.append(f"| {wid} | {kg_s} | {sheaf_s} | {speedup_s} |")
        lines.append("")
        errors = [r for r in self.results if r.error]
        if errors:
            lines.append("## Errors\n")
            for e in errors:
                lines.append(f"- {e.workload_id}/{e.engine}: {e.error}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "latency": self.latency_table(),
            "result_counts": self.result_count_table(),
            "speedups": self.speedup_table(),
            "errors": [{"workload": r.workload_id, "engine": r.engine, "error": r.error}
                       for r in self.results if r.error],
        }


def contextual_benchmark_table(
    kg_stats: dict[str, ContextualMetrics],
    sheaf_stats: dict[str, ContextualMetrics],
) -> str:
    """Generate a LaTeX table comparing KG and SheafDB across workloads."""
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Contextual Benchmark Results}",
        r"\label{tab:contextual}",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Workload & KG (ms) & SheafDB (ms) & Speedup \\",
        r"\midrule",
    ]
    all_wids = sorted(set(kg_stats.keys()) | set(sheaf_stats.keys()))
    for wid in all_wids:
        kg_lat = kg_stats.get(wid, ContextualMetrics()).latency_ms
        sh_lat = sheaf_stats.get(wid, ContextualMetrics()).latency_ms
        speedup = kg_lat / sh_lat if sh_lat > 0 else float("inf")
        speedup_s = f"{speedup:.2f}$\\times$" if speedup < 1000 else "—"
        lines.append(f"{wid} & {kg_lat:.2f} & {sh_lat:.2f} & {speedup_s} \\\\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])
    return "\n".join(lines)


def contextual_radar_data(
    kg_metrics: dict[str, ContextualMetrics],
    sheaf_metrics: dict[str, ContextualMetrics],
) -> dict[str, dict[str, float]]:
    """Prepare data for a radar chart comparing engines across workload types."""
    categories = ["contextual", "high-arity", "temporal", "provenance", "consistency", "mixed"]
    data: dict[str, dict[str, float]] = {"KnowledgeGraph": {}, "SheafDatabase": {}}
    for engine, metrics_dict in [("KnowledgeGraph", kg_metrics), ("SheafDatabase", sheaf_metrics)]:
        for cat in categories:
            cat_wids = {wid for wid, m in metrics_dict.items() if cat in wid.lower()}
            if cat_wids:
                avg = sum(metrics_dict[wid].latency_ms for wid in cat_wids) / len(cat_wids)
                data[engine][cat] = avg
            else:
                data[engine][cat] = 0.0
    return data
