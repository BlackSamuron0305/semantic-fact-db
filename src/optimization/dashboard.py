"""Performance dashboard — HTML, CSV, JSON report generation.

Combines ablation, sensitivity, scalability, memory, and hotspot
results into a single self-contained HTML dashboard, CSV tables,
and a JSON data bundle.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ablation import AblationResult
from .sensitivity import SensitivityResult
from .scalability import ScalabilityResult
from .memory import MemoryReport
from .hotspot import HotspotReport
from .manager import OptimizationManager
from .report import OptimizationReport


@dataclass
class PerformanceDashboard:
    manager_report: OptimizationReport | None = None
    ablation: AblationResult | None = None
    sensitivities: list[SensitivityResult] = field(default_factory=list)
    scalability: ScalabilityResult | None = None
    memory: MemoryReport | None = None
    hotspot: HotspotReport | None = None
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self, path: str | Path) -> str:
        data = {
            "generated_at": self.generated_at,
            "metadata": self.metadata,
            "optimization_report": self.manager_report.to_dict() if self.manager_report else None,
            "ablation": self.ablation.to_dict() if self.ablation else None,
            "sensitivities": [s.to_dict() for s in self.sensitivities],
            "scalability": self.scalability.to_dict() if self.scalability else None,
            "memory": self.memory.to_dict() if self.memory else None,
            "hotspot": self.hotspot.to_dict() if self.hotspot else None,
        }
        path = Path(path)
        path.write_text(json.dumps(data, indent=2, default=str))
        return str(path)

    def to_csv(self, output_dir: str | Path) -> list[str]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []

        if self.ablation:
            csv_path = out_dir / "ablation.csv"
            with open(csv_path, "w") as f:
                f.write("enabled,disabled,latency_ms,memory_bytes\n")
                for run in self.ablation.runs:
                    enabled = " ".join(run.enabled_set)
                    disabled = " ".join(run.disabled_set)
                    f.write(f"{enabled},{disabled},{run.latency_ms},{run.memory_bytes}\n")
            written.append(str(csv_path))

        if self.sensitivities:
            for sens in self.sensitivities:
                csv_path = out_dir / f"sensitivity_{sens.parameter_name}.csv"
                with open(csv_path, "w") as f:
                    f.write("value,latency_ms,memory_bytes,throughput_qps,hit_rate\n")
                    for p in sens.points:
                        f.write(f"{p.parameter_value},{p.latency_ms},{p.memory_bytes},{p.throughput_qps},{p.hit_rate}\n")
                written.append(str(csv_path))

        if self.scalability:
            for dim in self.scalability.dimensions:
                csv_path = out_dir / f"scalability_{dim.name}.csv"
                with open(csv_path, "w") as f:
                    f.write("scale,latency_ms,memory_bytes,throughput_qps\n")
                    for p in dim.points:
                        f.write(f"{p.scale_value},{p.latency_ms},{p.memory_bytes},{p.throughput_qps}\n")
                written.append(str(csv_path))

        if self.hotspot:
            csv_path = out_dir / "hotspot.csv"
            with open(csv_path, "w") as f:
                f.write("name,total_time_ns,call_count,avg_time_ns,memory_bytes\n")
                for e in self.hotspot.entries:
                    f.write(f"{e.name},{e.total_time_ns},{e.call_count},{e.avg_time_ns},{e.total_memory_bytes}\n")
            written.append(str(csv_path))

        return written

    def to_html(self, path: str | Path) -> str:
        data_json = json.dumps(self.to_dict(), indent=2, default=str)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SheafDB Performance Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 2rem; background: #f8f9fa; color: #333; }}
  h1, h2, h3 {{ color: #1a1a2e; }}
  .card {{ background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 1.5rem; margin-bottom: 1.5rem; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem; }}
  .stat {{ background: #e9ecef; padding: 1rem; border-radius: 6px; text-align: center; }}
  .stat-value {{ font-size: 1.8rem; font-weight: bold; color: #0d6efd; }}
  .stat-label {{ font-size: 0.85rem; color: #6c757d; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem; text-align: left; border-bottom: 1px solid #dee2e6; }}
  th {{ background: #f1f3f5; font-weight: 600; }}
  tr:hover {{ background: #f8f9fa; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem; }}
  .badge-on {{ background: #d3f9d8; color: #2b8a3e; }}
  .badge-off {{ background: #ffe3e3; color: #c92a2a; }}
  .bar-container {{ background: #e9ecef; height: 20px; border-radius: 10px; margin: 0.5rem 0; }}
  .bar-fill {{ height: 100%; border-radius: 10px; background: #0d6efd; text-align: center; color: #fff; font-size: 0.75rem; line-height: 20px; }}
  .section-title {{ border-bottom: 2px solid #dee2e6; padding-bottom: 0.5rem; margin-top: 2rem; }}
</style>
</head>
<body>
<h1>SheafDB Performance Dashboard</h1>
<p>Generated: {self.generated_at}</p>
"""

        # Overview stats
        html += '<div class="card"><h2>Overview</h2><div class="stats">'

        if self.manager_report:
            html += f"""
            <div class="stat"><div class="stat-value">{self.manager_report.enabled_count}/{self.manager_report.total_optimizations}</div><div class="stat-label">Optimizations Active</div></div>
            <div class="stat"><div class="stat-value">{self.manager_report.profile_name}</div><div class="stat-label">Profile</div></div>
            """

        if self.ablation:
            html += f"""
            <div class="stat"><div class="stat-value">{self.ablation.n_runs}</div><div class="stat-label">Ablation Runs</div></div>
            <div class="stat"><div class="stat-value">{self.ablation.baseline_latency_ms:.2f} ms</div><div class="stat-label">Baseline Latency</div></div>
            """

        if self.hotspot:
            html += f"""
            <div class="stat"><div class="stat-value">{len(self.hotspot.entries)}</div><div class="stat-label">Hotspots Tracked</div></div>
            <div class="stat"><div class="stat-value">{self.hotspot.total_time_ms:.1f} ms</div><div class="stat-label">Total Hotspot Time</div></div>
            """

        if self.memory:
            html += f"""
            <div class="stat"><div class="stat-value">{self.memory.total_deep / 1024:.1f} KB</div><div class="stat-label">Total Memory (Deep)</div></div>
            """

        html += '</div></div>'

        if self.manager_report:
            html += '<div class="card"><h2>Optimization Report</h2>'
            html += '<table><thead><tr><th>Name</th><th>Engine</th><th>Category</th><th>Status</th><th>Hits</th><th>Misses</th><th>Hit Rate</th><th>Memory</th></tr></thead><tbody>'
            for name, state in sorted(self.manager_report.states.items()):
                e = state.entry
                status = '<span class="badge badge-on">ON</span>' if state.enabled else '<span class="badge badge-off">OFF</span>'
                hr = f"{state.hit_rate:.1%}" if state.hit_count + state.miss_count > 0 else "N/A"
                mem = f"{state.memory_estimate_bytes / 1024:.1f} KB" if state.memory_estimate_bytes else "-"
                html += f"<tr><td><code>{name}</code></td><td>{e.engine}</td><td>{e.category}</td><td>{status}</td><td>{state.hit_count}</td><td>{state.miss_count}</td><td>{hr}</td><td>{mem}</td></tr>"
            html += '</tbody></table></div>'

        if self.ablation:
            html += '<div class="card"><h2>Ablation Study</h2>'
            html += '<table><thead><tr><th>Disabled</th><th>Latency (ms)</th><th>Speedup vs Baseline</th><th>Memory (KB)</th></tr></thead><tbody>'
            for run in sorted(self.ablation.runs, key=lambda r: r.latency_ms, reverse=True)[:20]:
                speedup = self.ablation.baseline_latency_ms / max(0.001, run.latency_ms)
                disabled = ", ".join(run.disabled_set) if run.disabled_set else "(none added)"
                html += f"<tr><td><code>{disabled}</code></td><td>{run.latency_ms:.3f}</td><td>{speedup:.2f}x</td><td>{run.memory_bytes / 1024:.1f}</td></tr>"
            html += '</tbody></table></div>'

        if self.sensitivities:
            html += '<div class="card"><h2>Sensitivity Analysis</h2>'
            for sens in self.sensitivities:
                html += f'<h3>{sens.parameter_name}</h3>'
                html += '<table><thead><tr><th>Value</th><th>Latency (ms)</th><th>Memory (KB)</th><th>Throughput (qps)</th></tr></thead><tbody>'
                for p in sens.points:
                    html += f"<tr><td>{p.parameter_value}</td><td>{p.latency_ms:.3f}</td><td>{p.memory_bytes/1024:.1f}</td><td>{p.throughput_qps:.1f}</td></tr>"
                html += '</tbody></table>'
            html += '</div>'

        if self.scalability:
            html += '<div class="card"><h2>Scalability Analysis</h2>'
            for dim in self.scalability.dimensions:
                html += f'<h3>{dim.name} <span class="badge badge-on">{dim.scaling_behavior}</span></h3>'
                html += '<table><thead><tr><th>Scale</th><th>Latency (ms)</th><th>Memory (KB)</th></tr></thead><tbody>'
                for p in dim.points[:10]:
                    html += f"<tr><td>{p.scale_value}</td><td>{p.latency_ms:.3f}</td><td>{p.memory_bytes/1024:.1f}</td></tr>"
                html += '</tbody></table>'
            html += '</div>'

        if self.hotspot:
            html += '<div class="card"><h2>Hotspot Analysis</h2>'
            html += '<table><thead><tr><th>Name</th><th>Total (ms)</th><th>Calls</th><th>Avg (ms)</th><th>Memory (KB)</th></tr></thead><tbody>'
            for e in self.hotspot.top_k(20):
                html += f"<tr><td><code>{e.name}</code></td><td>{e.total_time_ms:.3f}</td><td>{e.call_count}</td><td>{e.avg_time_ms:.4f}</td><td>{e.total_memory_bytes/1024:.1f}</td></tr>"
            html += '</tbody></table></div>'

        if self.memory:
            html += '<div class="card"><h2>Memory Analysis</h2>'
            html += '<table><thead><tr><th>Name</th><th>Deep Size (KB)</th><th>Items</th><th>Note</th></tr></thead><tbody>'
            for e in self.memory.top_k():
                html += f"<tr><td><code>{e.name}</code></td><td>{e.deep_bytes/1024:.1f}</td><td>{e.item_count}</td><td>{e.note}</td></tr>"
            html += '</tbody></table></div>'

        html += """
<div class="card">
  <h2>Data Export</h2>
  <p>The full dashboard data is available as <a href="dashboard.json">JSON</a> and CSV files in the output directory.</p>
</div>
</body></html>"""

        path = Path(path)
        path.write_text(html)
        log = logging.getLogger(__name__)
        log.info("Dashboard written to %s", path)
        return str(path)

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps({
            "generated_at": self.generated_at,
            "metadata": self.metadata,
            "optimization_report": self.manager_report.to_dict() if self.manager_report else None,
            "ablation": self.ablation.to_dict() if self.ablation else None,
            "sensitivities": [s.to_dict() for s in self.sensitivities],
            "scalability": self.scalability.to_dict() if self.scalability else None,
            "memory": self.memory.to_dict() if self.memory else None,
            "hotspot": self.hotspot.to_dict() if self.hotspot else None,
        }, default=str))
