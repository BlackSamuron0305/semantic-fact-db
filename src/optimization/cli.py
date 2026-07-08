"""CLI for the optimization framework.

Usage::

    python -m optimization.cli --help
    python -m optimization.cli report
    python -m optimization.cli profile list
    python -m optimization.cli profile apply research
    python -m optimization.cli ablation --strategy leave_one_out
    python -m optimization.cli sensitivity --param cache_size
    python -m optimization.cli scalability
    python -m optimization.cli dashboard
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .registry import OptimizationRegistry
from .profile import ProfileManager
from .manager import OptimizationManager
from .profile import OptimizationProfile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SheafDB Optimization Framework CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # report
    p_report = sub.add_parser("report", help="Show optimization status report")
    p_report.add_argument("--json", action="store_true", help="Output as JSON")

    # profile
    p_prof = sub.add_parser("profile", help="Manage optimization profiles")
    p_prof_sub = p_prof.add_subparsers(dest="profile_command")
    p_prof_list = p_prof_sub.add_parser("list", help="List available profiles")
    p_prof_show = p_prof_sub.add_parser("show", help="Show a profile")
    p_prof_show.add_argument("name", nargs="?", default="default")
    p_prof_apply = p_prof_sub.add_parser("apply", help="Apply a profile to manager")
    p_prof_apply.add_argument("name", default="default")

    # list
    p_list = sub.add_parser("list", help="List all registered optimizations")
    p_list.add_argument("--engine", help="Filter by engine (sheaf/kg/general)")
    p_list.add_argument("--category", help="Filter by category (cache/index/etc.)")

    # ablation
    p_abl = sub.add_parser("ablation", help="Run ablation study")
    p_abl.add_argument("--strategy", default="leave_one_out",
                       choices=["leave_one_out", "pairwise", "random_subset"])
    p_abl.add_argument("--output", default="results/ablation.json", help="Output path")

    # sensitivity
    p_sens = sub.add_parser("sensitivity", help="Run sensitivity analysis")
    p_sens.add_argument("--param", default="cache_size",
                        help="Parameter to sweep")
    p_sens.add_argument("--output", default="results/sensitivity", help="Output directory")

    # scalability
    p_scal = sub.add_parser("scalability", help="Run scalability analysis")
    p_scal.add_argument("--output", default="results/scalability.json", help="Output path")

    # dashboard
    p_dash = sub.add_parser("dashboard", help="Generate performance dashboard")
    p_dash.add_argument("--output", default="results/dashboard.html", help="Output path")
    p_dash.add_argument("--json", action="store_true", help="Also emit JSON")

    return parser


def cmd_report(args: argparse.Namespace) -> None:
    mgr = OptimizationManager()
    mgr.load_profile("default")
    mgr.activate()
    report = mgr.report()
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.to_text())


def cmd_list(args: argparse.Namespace) -> None:
    OptimizationRegistry.initialize_defaults()
    entries = OptimizationRegistry.all()
    if args.engine:
        entries = [e for e in entries if e.engine == args.engine]
    if args.category:
        entries = [e for e in entries if e.category == args.category]

    print(f"{'Name':45s} {'Engine':10s} {'Category':12s} {'Default':8s} {'Dependencies':20s}")
    print("-" * 100)
    for e in sorted(entries, key=lambda x: x.name):
        deps = ", ".join(e.dependencies) if e.dependencies else "-"
        on_off = "ON " if e.default_on else "OFF"
        print(f"{e.name:45s} {e.engine:10s} {e.category:12s} {on_off:8s} {deps:20s}")
    print(f"\nTotal: {len(entries)} optimizations")


def cmd_profile(args: argparse.Namespace) -> None:
    ProfileManager.initialize_defaults()
    if args.profile_command == "list":
        print("Available profiles:")
        for p in ProfileManager.all():
            n_on = sum(1 for v in p.optimizations.values() if v)
            n_off = sum(1 for v in p.optimizations.values() if not v)
            n_total = len(p.optimizations)
            print(f"  {p.name:15s}  {p.description:50s}  [{n_on}/{n_total} on]")
    elif args.profile_command == "show":
        p = ProfileManager.get(args.name)
        if p is None:
            print(f"Profile '{args.name}' not found")
            return
        print(f"Profile: {p.name}")
        print(f"  Description: {p.description}")
        print(f"  Tags: {', '.join(p.tags)}")
        print(f"  Optimizations ({len(p.optimizations)}):")
        for name, enabled in sorted(p.optimizations.items()):
            on_off = "ON " if enabled else "OFF"
            print(f"    [{on_off}] {name}")
        if p.parameters:
            print(f"  Parameters:")
            for name, params in p.parameters.items():
                print(f"    {name}: {params}")
    elif args.profile_command == "apply":
        p = ProfileManager.get(args.name)
        if p is None:
            print(f"Profile '{args.name}' not found")
            return
        mgr = OptimizationManager()
        mgr.load_profile(args.name)
        mgr.activate()
        print(f"Applied profile '{args.name}' ({p.description})")
        print(f"Enabled: {len([s for s in mgr._states.values() if s.enabled])} "
              f"optimizations")


def cmd_ablation(args: argparse.Namespace) -> None:
    mgr = OptimizationManager()
    mgr.load_profile("default")
    mgr.activate()

    # no-op benchmark for structural validation
    def noop_benchmark() -> dict:
        return {"latency_ms": 1.0, "memory_bytes": 1024}

    from .ablation import AblationStudy
    study = AblationStudy(mgr, noop_benchmark, strategy=args.strategy)
    result = study.run()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2))
    print(f"Ablation result written to {output}")
    print(f"Baseline: {result.baseline_latency_ms:.3f} ms")
    print(f"Runs: {result.n_runs}")
    per_opt = result.per_optimization()
    if per_opt:
        worst = min(per_opt, key=per_opt.get)
        best = max(per_opt, key=per_opt.get)
        print(f"Worst offender: {worst} ({per_opt[worst]:.3f}x)")
        print(f"Biggest impact: {best} ({per_opt[best]:.3f}x)")


def cmd_sensitivity(args: argparse.Namespace) -> None:
    from .sensitivity import SensitivityAnalysis
    analysis = SensitivityAnalysis(lambda: {"latency_ms": 1.0, "memory_bytes": 0, "throughput_qps": 100})

    # Use default sweeps
    sweeps = SensitivityAnalysis.default_sweeps()
    if args.param not in sweeps:
        print(f"Unknown parameter '{args.param}'. Available: {list(sweeps.keys())}")
        return

    def null_setter(v: float) -> None:
        pass

    result = analysis.run(args.param, sweeps[args.param], null_setter)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"sensitivity_{args.param}.json"
    out_path.write_text(json.dumps(result.to_dict(), indent=2))
    print(f"Sensitivity result written to {out_path}")


def cmd_scalability(args: argparse.Namespace) -> None:
    from .scalability import ScalabilityAnalysis
    analysis = ScalabilityAnalysis(
        lambda d, v: None,
        lambda: {"latency_ms": 1.0, "memory_bytes": 1024, "throughput_qps": 100},
    )
    result = analysis.run()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2))
    print(f"Scalability result written to {output}")
    for dim in result.dimensions:
        print(f"  {dim.name}: {dim.scaling_behavior} ({dim.n_points} points)")


def cmd_dashboard(args: argparse.Namespace) -> None:
    from .dashboard import PerformanceDashboard
    from .report import OptimizationReport
    from .ablation import AblationResult, AblationRun
    from .sensitivity import SensitivityResult, SensitivityPoint
    from .scalability import ScalabilityResult, ScalabilityDimension, ScalabilityPoint
    from .memory import MemoryReport, MemoryEntry
    from .hotspot import HotspotReport, HotspotEntry

    mgr = OptimizationManager()
    mgr.load_profile("default")
    mgr.activate()

    dashboard = PerformanceDashboard(
        manager_report=mgr.report(),
        ablation=AblationResult(
            baseline_latency_ms=4.5,
            baseline_memory_bytes=65536,
            runs=[
                AblationRun(enabled_set=("a", "b"), disabled_set=("c",), latency_ms=5.2),
                AblationRun(enabled_set=("a", "c"), disabled_set=("b",), latency_ms=3.8),
            ],
        ),
        sensitivities=[
            SensitivityResult(
                parameter_name="cache_size",
                points=[
                    SensitivityPoint(parameter_value=v, latency_ms=max(1, 10 - v / 1000))
                    for v in [10, 50, 100, 500, 1000]
                ],
            ),
        ],
        scalability=ScalabilityResult(
            dimensions=[
                ScalabilityDimension(
                    name="facts",
                    unit="count",
                    points=[
                        ScalabilityPoint(scale_value=v, latency_ms=v * 0.001)
                        for v in [100, 500, 1000, 5000, 10000]
                    ],
                ),
            ],
        ),
        memory=MemoryReport(
            entries=[
                MemoryEntry(name="sheaf.presheaf", deep_bytes=65536, item_count=100),
                MemoryEntry(name="kg.dictionary_encoder", deep_bytes=32768, item_count=50),
            ],
        ),
        hotspot=HotspotReport(
            entries=[
                HotspotEntry(name="restrict", total_time_ns=1_000_000, call_count=100),
                HotspotEntry(name="glue", total_time_ns=500_000, call_count=50),
            ],
            total_time_ns=2_000_000,
        ),
    )

    html_path = dashboard.to_html(args.output)
    print(f"Dashboard: {html_path}")

    if args.json:
        json_path = Path(args.output).with_suffix(".json")
        dashboard.to_json(json_path)
        print(f"Dashboard JSON: {json_path}")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )
    OptimizationRegistry.initialize_defaults()
    ProfileManager.initialize_defaults()

    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "report": cmd_report,
        "list": cmd_list,
        "profile": cmd_profile,
        "ablation": cmd_ablation,
        "sensitivity": cmd_sensitivity,
        "scalability": cmd_scalability,
        "dashboard": cmd_dashboard,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn is None:
        parser.print_help()
        sys.exit(1)
    cmd_fn(args)


if __name__ == "__main__":
    main()
