#!/usr/bin/env python3
"""Paper generation script.

Generates:
  - reproducibility macros (generated/*.tex)
  - placeholder figures (paper/figures/placeholder.pdf)
  - paper compilation via latexmk or pdflatex

Usage:
    uv run python scripts/generate_paper.py          # generate + compile
    uv run python scripts/generate_paper.py --compile-only
    uv run python scripts/generate_paper.py --generate-only
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = REPO_ROOT / "paper"
FIGURES_DIR = PAPER_DIR / "figures"
TABLES_DIR = PAPER_DIR / "tables"
GENERATED_DIR = PAPER_DIR / "generated"
BENCHMARK_PATH = REPO_ROOT / "results" / "benchmark.json"


def get_git_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_uv_lock_hash() -> str:
    lock_file = REPO_ROOT / "uv.lock"
    if lock_file.exists():
        import hashlib

        return hashlib.sha256(lock_file.read_bytes()).hexdigest()[:16]
    return "unknown"


def generate_reproducibility_macros() -> Path:
    """Write paper/generated/reproducibility.tex.

    Prefers the real manifest a benchmark run produces
    (results/paper_suite_reproducibility.json, written by
    ReproducibilityRecord and consumed identically by
    scripts/generate_tables.py) over guessing at hardware. Only falls
    back to live introspection -- never to hardcoded placeholder values --
    when no benchmark has been run yet, since a fabricated CPU/memory
    string is worse than an honestly-labelled "not yet run".
    """
    output = GENERATED_DIR / "reproducibility.tex"
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    repro_path = REPO_ROOT / "results" / "paper_suite_reproducibility.json"
    if repro_path.exists():
        repro = json.loads(repro_path.read_text())
        memory_gb = repro.get("memory_total", 0) / 1e9
        git_commit = (repro.get("git") or {}).get("commit", "unknown")[:7]
        content = f"""% Auto-generated reproducibility macros
% Source: results/paper_suite_reproducibility.json
\\providecommand{{\\generatedcpu}}{{{repro.get("cpu_model", "unknown")} ({repro.get("cpu_count", "?")} cores)}}
\\providecommand{{\\generatedmemory}}{{{memory_gb:.1f} GB}}
\\providecommand{{\\generatedos}}{{{repro.get("os", "unknown")} {repro.get("os_release", "")}}}
\\providecommand{{\\generatedhash}}{{{git_commit}}}
\\providecommand{{\\generatedpython}}{{{repro.get("python_version", "unknown")}}}
\\providecommand{{\\generateduvlock}}{{{repro.get("uv_lock", "unknown")}}}
\\providecommand{{\\generatedchecksum}}{{{repro.get("dataset_checksum", "unknown")}}}
\\providecommand{{\\generatedseed}}{{{repro.get("seed", "unknown")}}}
\\providecommand{{\\generateddate}}{{{repro.get("timestamp", "unknown")}}}
"""
        output.write_text(content)
        return output

    import psutil  # local import: only needed on this no-manifest-yet path

    now = datetime.now().isoformat()
    content = f"""% Auto-generated reproducibility macros
% Generated: {now}
% WARNING: no results/paper_suite_reproducibility.json found -- these are
% live-introspected values from THIS machine, not the benchmarked run.
% Run `uv run sfdb benchmark` first to get the real manifest.
\\providecommand{{\\generatedcpu}}{{{platform.processor() or "unknown"} ({psutil.cpu_count(logical=True)} cores)}}
\\providecommand{{\\generatedmemory}}{{{psutil.virtual_memory().total / 1e9:.1f} GB}}
\\providecommand{{\\generatedos}}{{{platform.system()} {platform.release()}}}
\\providecommand{{\\generatedhash}}{{{get_git_hash()}}}
\\providecommand{{\\generatedpython}}{{{get_python_version()}}}
\\providecommand{{\\generateduvlock}}{{{get_uv_lock_hash()}}}
\\providecommand{{\\generatedchecksum}}{{not-yet-run}}
\\providecommand{{\\generatedseed}}{{42}}
\\providecommand{{\\generateddate}}{{{now}}}
"""
    output.write_text(content)
    return output


def generate_placeholder_figures() -> list[Path]:
    """Generate placeholder figures if benchmark results not available."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    figure_names = [
        "latency",
        "throughput",
        "scaling",
        "scalability",
        "speedup",
        "cdf",
        "memory",
        "storage",
        "architecture",
        "topology",
        "restriction",
    ]
    for name in figure_names:
        path = FIGURES_DIR / f"{name}.pdf"
        if not path.exists():
            _create_placeholder_pdf(path)
            generated.append(path)
    return generated


def _create_placeholder_pdf(path: Path) -> None:
    """Create a minimal placeholder PDF."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(
            0.5,
            0.5,
            f"Placeholder: {path.stem}\n(Run benchmarks to populate)",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        fig.savefig(str(path), bbox_inches="tight")
        plt.close(fig)
    except ImportError:
        _create_minimal_pdf(path)


def _create_minimal_pdf(path: Path) -> None:
    """Create a truly minimal PDF without matplotlib."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<<>>>>endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n"
        b"190\n"
        b"%%EOF"
    )
    path.write_bytes(content)


def generate_tables_from_benchmarks() -> list[Path]:
    """Generate LaTeX tables from benchmark results if available."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    # Copy existing benchmark LaTeX tables to paper/tables/
    for d in sorted(REPO_ROOT.glob("results/*/")):
        name = d.name
        table_src = d / f"{name}_table.tex"
        if table_src.exists():
            dest = TABLES_DIR / f"{name}_table.tex"
            dest.write_text(table_src.read_text())
            generated.append(dest)

    if not BENCHMARK_PATH.exists():
        generated.extend(TABLES_DIR.glob("*.tex"))
        return generated

    data = json.loads(BENCHMARK_PATH.read_text())
    meta = data.pop("_meta", {})

    # Summary table — average latency per engine across all queries/queries
    engines = sorted(set(
        eng for b in data.values()
        for eng in b.get("summary", {}).keys()
    ))
    queries = sorted(set(
        q for b in data.values()
        for qs in b.get("summary", {}).values()
        for q in qs.keys()
    ))

    # Build summary table: benchmark × engine (mean latency)
    summary_lines = [
        r"\toprule",
        "Benchmark & " + " & ".join(engines) + r" \\",
        r"\midrule",
    ]
    for name, b in sorted(data.items()):
        row = [name]
        for eng in engines:
            if eng in b.get("summary", {}):
                vals = [v["mean"] for v in b["summary"][eng].values()]
                row.append(f"{np.mean(vals)*1000:.1f}" if vals else "--")
            else:
                row.append("--")
        row.append(r"\\")
        summary_lines.append(" & ".join(row))
    summary_lines.append(r"\bottomrule")

    summary_content = (
        r"% Auto-generated summary table from benchmark results" + "\n"
        r"\begin{tabular}{@{}l" + "c" * len(engines) + r"@{}}" + "\n"
        + "\n".join(summary_lines) + "\n"
        r"\end{tabular}" + "\n"
    )
    summary_path = TABLES_DIR / "summary.tex"
    summary_path.write_text(summary_content)
    generated.append(summary_path)

    # Verification table
    verified_all = meta.get("all_verified", False)
    if verified_all:
        verif_content = (
            r"% Auto-generated verification status" + "\n"
            r"\begin{tabular}{@{}lc@{}}" + "\n"
            r"\toprule" + "\n"
            "Query Equivalence & Passed \\\\" + "\n"
            r"\midrule" + "\n"
            f"All {meta.get('total_rows', 0)} queries & \\checkmark \\\\" + "\n"
            r"\bottomrule" + "\n"
            r"\end{tabular}" + "\n"
        )
    else:
        verif_content = (
            r"% Auto-generated verification status" + "\n"
            r"\begin{tabular}{@{}lc@{}}" + "\n"
            r"\toprule" + "\n"
            "Query Equivalence & Failed \\\\" + "\n"
            r"\midrule" + "\n"
            f"Some queries diverged & \\texttimes \\\\" + "\n"
            r"\bottomrule" + "\n"
            r"\end{tabular}" + "\n"
        )
    verif_path = TABLES_DIR / "verification.tex"
    verif_path.write_text(verif_content)
    generated.append(verif_path)

    data["_meta"] = meta
    return generated


def _generate_placeholder_table(path: Path, label: str) -> None:
    content = f"""% Placeholder table: {label}
% Auto-generated by scripts/generate_paper.py
\\begin{{tabular}}{{@{{}}lccc@{{}}}}
\\toprule
Dataset & KG & SheafDB & Speedup \\\\
\\midrule
\\multicolumn{{4}}{{c}}{{\\emph{{Run benchmarks to populate}}}} \\\\
\\bottomrule
\\end{{tabular}}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def compile_paper() -> bool:
    """Compile the LaTeX paper."""
    import os

    orig_dir = os.getcwd()
    os.chdir(str(PAPER_DIR))
    try:
        result = subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "main.tex"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print("=== LaTeX stdout ===")
            print(result.stdout[-2000:])
            print("=== LaTeX stderr ===")
            print(result.stderr[-2000:])
            return False
        return True
    except FileNotFoundError:
        try:
            result = subprocess.run(
                ["tectonic", "--keep-logs", "--keep-intermediates", "main.tex"],
                capture_output=True,
                text=True,
                timeout=900,
                cwd=str(PAPER_DIR),
            )
            if result.returncode != 0:
                print("=== Tectonic stdout ===")
                print(result.stdout[-2000:])
                print("=== Tectonic stderr ===")
                print(result.stderr[-2000:])
                return False
            return True
        except FileNotFoundError:
            # fall back to pdflatex/bibtex directly
            try:
                for _ in range(2):
                    r = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=str(PAPER_DIR),
                    )
                    if r.returncode != 0:
                        print(r.stdout[-1000:])
                        print(r.stderr[-1000:])
                        return False
                # bibtex
                subprocess.run(
                    ["bibtex", "main"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(PAPER_DIR),
                )
                for _ in range(2):
                    r = subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "main.tex"],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd=str(PAPER_DIR),
                    )
                return True
            except FileNotFoundError:
                print(
                    "ERROR: No supported TeX engine found. Install latexmk, tectonic, or pdflatex."
                )
                return False
    except Exception as e:
        print(f"ERROR during compilation: {e}")
        return False
    finally:
        os.chdir(orig_dir)


def clean() -> None:
    try:
        subprocess.run(
            ["latexmk", "-C"],
            capture_output=True,
            text=True,
            cwd=str(PAPER_DIR),
        )
    except FileNotFoundError:
        pass
    for ext in ["*.aux", "*.log", "*.out", "*.bbl", "*.blg", "*.fls", "*.fdb_latexmk"]:
        for f in PAPER_DIR.glob(ext):
            f.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and compile the paper")
    parser.add_argument("--compile-only", action="store_true", help="Only compile")
    parser.add_argument("--generate-only", action="store_true", help="Only generate")
    parser.add_argument("--clean", action="store_true", help="Clean auxiliary files")
    args = parser.parse_args()

    if args.clean:
        clean()
        return

    if args.compile_only:
        success = compile_paper()
        sys.exit(0 if success else 1)

    if args.generate_only:
        generate_reproducibility_macros()
        generate_placeholder_figures()
        generate_tables_from_benchmarks()
        print("Paper artifacts generated.")
        return

    # Full pipeline
    print("Generating reproducibility macros...")
    generate_reproducibility_macros()
    print("Generating placeholder figures...")
    generate_placeholder_figures()
    print("Generating tables...")
    generate_tables_from_benchmarks()
    print("Compiling paper...")
    success = compile_paper()
    if success:
        print(f"Paper compiled: {PAPER_DIR / 'main.pdf'}")
    else:
        print("Paper compilation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
