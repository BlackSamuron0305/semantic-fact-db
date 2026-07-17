"""SFDB CLI — command-line interface for the Semantic Fact Database.

Usage:
    sfdb init [--db PATH]
    sfdb ingest [--format json|parquet] FILE
    sfdb import [--format json|parquet] FILE
    sfdb export [--format json|parquet] [--output FILE]
    sfdb benchmark [--size tiny|small|medium] [--runs N] [--warm-up N]
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
    size: Optional[str] = typer.Option(
        None, "--size", "-s",
        help="Run a single scale only (tiny=100, small=1000, medium=10000). "
             "Omit to run the full paper suite (100, 1000, 10000).",
    ),
    runs: int = typer.Option(10, "--runs", help="Timed runs per query class / insert."),
    warm_up: int = typer.Option(2, "--warm-up", help="Untimed warm-up iterations before timing."),
    output_dir: str = typer.Option("results", "--output-dir", "-o", help="Output directory."),
) -> None:
    """Run the paper's benchmark suite: insert throughput plus LOOKUP,
    GLOBAL, and TEMPORAL query classes against real KnowledgeGraph and
    SheafDatabase engines, with cross-engine verification on every
    query class at every scale. This is the same command referenced in
    paper/sections/artifact.tex to reproduce the paper's numbers.
    """
    from sfdb.benchmark.paper_suite import PAPER_SCALES, run_paper_suite

    size_to_n = {"tiny": 100, "small": 1000, "medium": 10000}
    if size and size not in size_to_n:
        typer.echo(f"Unknown --size {size!r}; choose from {list(size_to_n)}", err=True)
        raise typer.Exit(1)
    scales = (size_to_n[size],) if size else PAPER_SCALES

    typer.echo(f"Running benchmark suite at scales {scales} ({runs} runs, {warm_up} warm-up)")
    result = run_paper_suite(
        output_dir=output_dir, scales=scales, num_runs=runs, warm_up=warm_up
    )

    status = "PASSED" if result["all_verified"] else "FAILED"
    typer.echo(f"Cross-engine verification: {status}")
    typer.echo(f"Results written to {output_dir}/paper_suite.* and paper_suite_summary.json")
    if not result["all_verified"]:
        raise typer.Exit(1)


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
