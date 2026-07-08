"""Benchmark output serialization — CSV, JSON, Parquet, Markdown, LaTeX."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from sfdb.benchmark.statistics import Statistics


@dataclass
class BenchOutputRow:
    engine: str = ""
    query: str = ""
    run: int = 0
    latency_ms: float = 0.0
    memory_bytes: int = 0
    cpu_percent: float = 0.0
    gc_collections: int = 0
    disk_read: int = 0
    disk_write: int = 0
    cache_hit: bool = False
    outlier: bool = False
    verified: bool = True


class OutputWriter:
    def __init__(self, output_dir: str = "results") -> None:
        self._dir = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._rows: list[BenchOutputRow] = []

    def add(self, row: BenchOutputRow) -> None:
        self._rows.append(row)

    def add_batch(self, rows: list[BenchOutputRow]) -> None:
        self._rows.extend(rows)

    def rows(self) -> list[BenchOutputRow]:
        return list(self._rows)

    def clear(self) -> None:
        self._rows.clear()

    def to_csv(self, name: str = "benchmark") -> str:
        path = self._dir / f"{name}.csv"
        with open(path, "w", newline="") as f:
            if not self._rows:
                return str(path)
            writer = csv.DictWriter(f, fieldnames=asdict(self._rows[0]).keys())
            writer.writeheader()
            for r in self._rows:
                writer.writerow(asdict(r))
        return str(path)

    def to_json(self, name: str = "benchmark") -> str:
        path = self._dir / f"{name}.json"
        path.write_text(json.dumps([asdict(r) for r in self._rows], indent=2))
        return str(path)

    def to_parquet(self, name: str = "benchmark") -> str:
        path = self._dir / f"{name}.parquet"
        try:
            import pandas as pd

            df = pd.DataFrame([asdict(r) for r in self._rows])
            df.to_parquet(str(path), index=False)
        except ImportError:
            pass
        return str(path)

    def to_markdown(self, name: str = "benchmark") -> str:
        path = self._dir / f"{name}.md"
        if not self._rows:
            path.write_text("No data\n")
            return str(path)
        cols = list(asdict(self._rows[0]).keys())
        lines = ["| " + " | ".join(cols) + " |"]
        lines.append("| " + " | ".join("---" for _ in cols) + " |")
        for r in self._rows:
            d = asdict(r)
            lines.append("| " + " | ".join(str(d[c]) for c in cols) + " |")
        path.write_text("\n".join(lines) + "\n")
        return str(path)

    def to_latex_table(self, name: str = "benchmark_table") -> str:
        path = self._dir / f"{name}.tex"
        if not self._rows:
            path.write_text("% No data\n")
            return str(path)
        cols = ["Engine", "Query", "Latency (ms)", "Memory (MB)", "CPU (%)"]
        lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            "\\caption{Benchmark Results}",
            "\\label{tab:benchmark}",
            "\\begin{tabular}{lrrrr}",
            "\\toprule",
            " & ".join(cols) + " \\\\",
            "\\midrule",
        ]
        for r in self._rows:
            lines.append(
                f"{r.engine} & {r.query} & {r.latency_ms:.2f} & {r.memory_bytes / 1e6:.2f} & {r.cpu_percent:.1f} \\\\"
            )
        lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}"])
        path.write_text("\n".join(lines) + "\n")
        return str(path)

    def to_summary_table(
        self, stats: dict[str, dict[str, Statistics]], name: str = "summary"
    ) -> str:
        path = self._dir / f"{name}.tex"
        lines = [
            "\\begin{table}[htbp]",
            "\\centering",
            "\\caption{Benchmark Summary (95\\% CI)}",
            "\\label{tab:summary}",
            "\\begin{tabular}{lrrrr}",
            "\\toprule",
            "Engine & Query & Mean (ms) & P95 (ms) & CI95 \\\\",
            "\\midrule",
        ]
        for engine_key in sorted(stats):
            for qid in sorted(stats[engine_key]):
                s = stats[engine_key][qid]
                lines.append(
                    f"{engine_key} & {qid} & {s.mean:.2f} & {s.p95:.2f} & [{s.ci95_low:.2f}, {s.ci95_high:.2f}] \\\\"
                )
        lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}"])
        path.write_text("\n".join(lines) + "\n")
        return str(path)
