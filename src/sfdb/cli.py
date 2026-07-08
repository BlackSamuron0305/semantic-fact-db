"""SFDB CLI — command-line interface for the Semantic Fact Database.

Usage:
    sfdb init [--db PATH]
    sfdb ingest [--format json|parquet] FILE
    sfdb import [--format json|parquet] FILE
    sfdb export [--format json|parquet] [--output FILE]
    sfdb benchmark [--config FILE] [--workloads C1,C2,...]
    sfdb profile [--config FILE]
    sfdb verify
    sfdb doctor
    sfdb paper [--output DIR]
    sfdb visualize [--output FILE]
    sfdb dashboard
    sfdb clean
    sfdb rebuild
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

import typer

app = typer.Typer(
    name="sfdb",
    help="Semantic Fact Database — sheaf-theoretic knowledge representation",
    add_completion=True,
    rich_markup_mode="rich",
)


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def _load_config(config_path: str | None) -> dict[str, Any]:
    if config_path is None:
        return {}
    import yaml
    p = Path(config_path)
    if not p.exists():
        typer.echo(f"Config not found: {p}", err=True)
        raise typer.Exit(1)
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _get_engine(db_path: str | None = None):
    from sfdb.sheaf.engine import SheafDatabaseEngine
    from sfdb.kg.engine import KnowledgeGraphEngine
    eng = SheafDatabaseEngine("sfdb_cli")
    eng.create({"db_path": db_path or ":memory:"})
    return eng


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.callback()
def main(ctx: typer.Context) -> None:
    """Semantic Fact Database — a sheaf-theoretic approach to knowledge representation."""
    pass


@app.command()
def init(
    db_path: str = typer.Option(":memory:", "--db", "-d", help="Database path (file or :memory:)"),
) -> None:
    """Initialize a new SFDB database."""
    eng = _get_engine(db_path)
    stats = eng.statistics()
    typer.echo(f"Initialized {eng.engine_type.value} at {db_path}")
    typer.echo(f"  Total facts: {stats.total_facts}")
    typer.echo(f"  Storage: {stats.storage_bytes} bytes")


@app.command()
def ingest(
    file: str = typer.Argument(..., help="Input file path"),
    fmt: str = typer.Option("json", "--format", "-f", help="Input format (json, parquet)"),
    db: str = typer.Option(":memory:", "--db", "-d", help="Database path"),
) -> None:
    """Ingest facts from a file into the database."""
    from sfdb.common.serialization import deserialize_json

    eng = _get_engine(db)
    p = Path(file)
    if not p.exists():
        typer.echo(f"File not found: {file}", err=True)
        raise typer.Exit(1)

    raw = p.read_bytes()
    if fmt == "json":
        facts_data = json.loads(raw)
        if isinstance(facts_data, dict):
            facts_data = [facts_data]
        from common.schema import SemanticFact
        from common.serialization import _dict_to_fact
        count = 0
        for d in facts_data:
            fact = _dict_to_fact(d)
            r = eng.insert(fact)
            if r.success:
                count += 1
        typer.echo(f"Ingested {count} facts from {file}")
    else:
        typer.echo(f"Unsupported format: {fmt}", err=True)
        raise typer.Exit(1)


@app.command()
def export_data(
    fmt: str = typer.Option("json", "--format", "-f", help="Output format (json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (stdout if not set)"),
    db: str = typer.Option(":memory:", "--db", "-d", help="Database path"),
) -> None:
    """Export facts from the database."""
    from common.interfaces import StorageFormat
    eng = _get_engine(db)
    sfmt = StorageFormat.JSON if fmt == "json" else StorageFormat.JSON
    data = eng.export(sfmt)
    if output:
        Path(output).write_bytes(data)
        typer.echo(f"Exported {len(data)} bytes to {output}")
    else:
        sys.stdout.buffer.write(data)


@app.command()
def benchmark(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Benchmark config file"),
    workloads: Optional[str] = typer.Option(None, "--workloads", "-w", help="Comma-separated workload IDs"),
    size: str = typer.Option("small", "--size", "-s", help="Dataset size (small, medium, large)"),
) -> None:
    """Run the benchmark suite."""
    from sfdb.benchmark.contextual.runner import ContextualBenchConfig, ContextualBenchRunner

    cfg = _load_config(config) if config else {}
    wl_list = [w.strip() for w in workloads.split(",")] if workloads else [
        "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"
    ]

    runner = ContextualBenchRunner(ContextualBenchConfig(
        dataset_size=size,
        workloads=tuple(wl_list),
        num_runs=3,
        output_dir=cfg.get("output_dir", "results/contextual"),
    ))
    typer.echo(f"Generating dataset ({size})...")
    runner.generate_dataset()
    typer.echo(f"Running {len(wl_list)} workloads...")
    reporter = runner.run()
    paths = runner.export()
    typer.echo(f"Results written to:")
    for name, p in paths.items():
        typer.echo(f"  {name}: {p}")


@app.command()
def profile(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Profile config"),
) -> None:
    """Profile database performance metrics."""
    cfg = _load_config(config) if config else {}
    eng = _get_engine(cfg.get("db"))
    stats = eng.benchmark_stats()
    for k, v in stats.items():
        typer.echo(f"  {k}: {v}")


@app.command()
def verify() -> None:
    """Run verification checks."""
    from sfdb.sheaf.engine import SheafDatabaseEngine
    from sfdb.kg.engine import KnowledgeGraphEngine

    for name, cls in [("KnowledgeGraph", KnowledgeGraphEngine), ("SheafDatabase", SheafDatabaseEngine)]:
        eng = cls(f"verify_{name}")
        eng.create()
        result = eng.verify()
        status = "[green]PASS[/green]" if result.valid else "[red]FAIL[/red]"
        typer.echo(f"{name:20s} {status}")
        for e in result.errors:
            typer.echo(f"  [red]ERROR[/red]: {e}")


@app.command()
def doctor() -> None:
    """System health check."""
    import platform
    import sys

    typer.echo(f"Python: {sys.version}")
    typer.echo(f"Platform: {platform.platform()}")
    typer.echo(f"uv available: {'Yes' if Path(sys.executable).parent.joinpath('uv').exists() else 'No'}")

    try:
        import numpy; typer.echo(f"numpy: {numpy.__version__}")
    except ImportError: typer.echo("numpy: [red]NOT FOUND[/red]")

    try:
        import scipy; typer.echo(f"scipy: {scipy.__version__}")
    except ImportError: typer.echo("scipy: [red]NOT FOUND[/red]")

    try:
        import rdflib; typer.echo(f"rdflib: {rdflib.__version__}")
    except ImportError: typer.echo("rdflib: [red]NOT FOUND[/red]")

    try:
        import networkx as nx; typer.echo(f"networkx: {nx.__version__}")
    except ImportError: typer.echo("networkx: [red]NOT FOUND[/red]")

    try:
        import matplotlib; typer.echo(f"matplotlib: {matplotlib.__version__}")
    except ImportError: typer.echo("matplotlib: [red]NOT FOUND[/red]")

    try:
        import duckdb; typer.echo(f"duckdb: {duckdb.__version__}")
    except ImportError: typer.echo("duckdb: [red]NOT FOUND[/red]")


@app.command()
def clean() -> None:
    """Remove generated artifacts (results, caches, compiled paper)."""
    import shutil

    dirs = ["results", ".hypothesis", ".mypy_cache", ".pytest_cache", ".ruff_cache"]
    for d in dirs:
        p = Path(d)
        if p.exists():
            shutil.rmtree(p)
            typer.echo(f"Removed {d}/")

    # Clean generated paper artifacts
    paper_gen = Path("paper/generated")
    if paper_gen.exists():
        shutil.rmtree(paper_gen)
        typer.echo(f"Removed paper/generated/")

    for pdf in Path("paper/figures").glob("*.pdf"):
        pdf.unlink()
        typer.echo(f"Removed {pdf}")


@app.command()
def dashboard() -> None:
    """Generate the benchmark dashboard HTML."""
    from sfdb.benchmark.dashboard import generate_dashboard
    generate_dashboard()
    typer.echo("Dashboard generated at results/dashboard.html")


@app.command()
def rebuild() -> None:
    """Clean all generated artifacts and rebuild from scratch."""
    clean()
    init()
    typer.echo("Rebuild complete.")


def main_cli() -> None:
    app()


if __name__ == "__main__":
    main_cli()
