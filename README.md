# Semantic Fact Database (SFDB)

A research prototype investigating whether indexing semantic facts by a
**context poset** (in the language of presheaves on a finite poset) offers a
more direct representation than the reification-plus-joins approach
conventional RDF triple stores use for high-arity and context-scoped facts.

On the finite, Alexandrov-topologised poset this system uses, the sheaf
condition holds vacuously — this is a presheaf database in the strict
technical sense. The paper (`paper/main.pdf`) does not claim a novel
sheaf-theoretic result; the value of the design is the context poset, the
stalk index, and the canonical cross-engine equivalence proof, not the
sheaf axioms. See `paper/sections/abstract.tex` for the full framing.

## Research Question

Can a context-indexed fact store answer entity-anchored queries faster than
a reified triple store, while remaining provably and verifiably equivalent
to it on every query both engines can answer?

## Quick Start

```bash
# Install dependencies
uv sync --group dev

# Run tests (347 tests)
uv run pytest

# Type check
uv run mypy src/

# Lint
uv run ruff check src/
```

## CLI Usage

```bash
# Initialize a database
uv run sfdb init

# Run the paper's benchmark suite (all 3 scales: 100, 1000, 10000 facts)
uv run sfdb benchmark

# Run a single scale for a quick check
uv run sfdb benchmark --size tiny --runs 3 --warm-up 1

# Verify database integrity
uv run sfdb verify

# Run diagnostics
uv run sfdb doctor

# Export data
uv run sfdb export --output data.json

# Clean generated artifacts
uv run sfdb clean
```

See `uv run sfdb --help` for all commands.

## Repository Structure

```
semantic-fact-db/
├── src/
│   └── sfdb/
│       ├── common/       # Base types, interfaces, schema
│       ├── kg/           # Knowledge Graph engine (reified-triple baseline)
│       ├── sheaf/        # Sheaf/presheaf-inspired engine
│       ├── query/        # Query language scaffolding (see note below)
│       ├── optimizer/    # Cost-based engine selector
│       ├── benchmark/    # Benchmark framework; paper_suite.py is the
│       │                 # single source of truth for the paper's numbers
│       ├── datasets/     # Dataset generators (arity, Zipf skew, temporal)
│       ├── visualization/ # Publication-quality plots
│       └── cli.py        # Command-line interface
├── tests/                # 347 unit tests
├── paper/                # LaTeX paper
├── research/             # Supporting proofs, notes, literature survey
├── docs/                 # Documentation
├── scripts/              # generate_tables.py / generate_figures.py
│                         # regenerate paper/tables and paper/figures from
│                         # results/paper_suite_summary.json
├── results/              # Generated benchmark outputs
├── pyproject.toml
├── CITATION.cff
└── README.md
```

**Note on `src/sfdb/query/`:** this package contains a fuller lexer/parser/
logical-plan/physical-plan pipeline that is not currently wired into either
engine's benchmark path; the benchmark harness drives both engines through
the typed `common.interfaces.Query` object directly. Treat the AST/optimizer
classes there as scaffolding, not as the query path the paper's numbers
exercise.

## Architecture

Two engines implement the `DatabaseEngine` ABC:

1. **KnowledgeGraphEngine** — reified triple-store baseline (SPO/POS/OSP
   indexes over SQLite, RDF-style reification for n-ary facts).
2. **SheafDatabaseEngine** — context-indexed engine (finite topological
   space over the context poset, stalk index, restriction cache).

### Sheaf Database Key Components

| Component | Description |
|-----------|-------------|
| `FiniteTopologicalSpace` | Open sets of facts grouped by semantic property |
| `Presheaf` | Sections over open sets with restriction maps |
| `ConsistencyChecker` | Defensive presheaf/sheaf axiom checks (vacuous by construction on this topology — see the paper) |
| `RestrictionGraph` | Directed acyclic graph of open set inclusions |
| `SheafOptimizer` | Query classification (local/semi-local/global) |
| `SheafQueryPlanner` | Restriction-based query execution |
| `StalkIndex` | Flat, hash-indexed fact table; backs both LOOKUP and GLOBAL queries |
| `GlobalSectionCache` | Cached gluing results |

## Benchmarks

`uv run sfdb benchmark` runs the paper's evaluation: insert throughput plus
three query classes, at three scales (100, 1,000, 10,000 facts), against
real `KnowledgeGraphEngine` and `SheafDatabaseEngine` instances, with
cross-engine result verification on every query class at every scale.

| Class | Description |
|-------|-------------|
| LOOKUP | Entity-anchored retrieval (subject match) |
| GLOBAL | Unrestricted full-scan queries |
| TEMPORAL | Bounded range queries over a fact's temporal envelope |

See `paper/sections/evaluation.tex` for the full methodology and results.

## Key Results

(See `paper/main.pdf` for the full evaluation; numbers below are from the
reported run and are regenerated by `scripts/generate_tables.py` from
`results/paper_suite_summary.json`.)

- **Insert**: SFDB is $0.74$–$0.99\times$ KG latency (essentially matched).
- **LOOKUP**: SFDB is $20$–$25\times$ faster than the KG baseline.
- **GLOBAL**: SFDB is $50$–$100\times$ faster.
- **TEMPORAL (bounded range)**: SFDB is $1.2$–$1.6\times$ faster.
- **Memory**: SFDB uses $1.3$–$4.8\times$ more resident memory per fact —
  this is the tradeoff that funds the latency advantages above.

## Dependencies

Runtime (25): numpy, scipy, pandas, pyarrow, duckdb, rdflib, networkx,
matplotlib, rich, typer, orjson, psutil, pydantic, pyyaml

Dev (6): pytest, pytest-cov, hypothesis, mypy, ruff, types-psutil, types-pyyaml

## Publication

See `paper/` for the full LaTeX paper. All tables and figures are
auto-generated from `results/paper_suite_summary.json` — see
`scripts/generate_tables.py` and `scripts/generate_figures.py`.

## Citation

```bibtex
@software{sfdb2026,
  title = {Semantic Fact Database (SFDB)},
  version = {0.1.0},
  year = {2026},
  url = {https://github.com/BlackSamuron0305/semantic-fact-db}
}
```

## License

MIT
