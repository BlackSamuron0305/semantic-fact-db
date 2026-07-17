# Semantic Fact Database (SFDB)

A research project investigating whether **sheaf theory** provides a more efficient
representation for semantic facts than traditional RDF-style knowledge graphs.

## Research Question

Can sheaf-theoretic representations preserve semantic equivalence while reducing
computational cost compared to RDF-style triple stores?

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

# Run benchmarks
uv run sfdb benchmark --size small

# Verify database integrity
uv run sfdb verify

# Run diagnostics
uv run sfdb doctor

# Generate dashboard
uv run sfdb dashboard

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
│       ├── canonical/    # Canonical model
│       ├── kg/           # Knowledge Graph engine (baseline)
│       ├── sheaf/        # Sheaf Database engine (experimental)
│       ├── query/        # Unified query language
│       ├── optimizer/    # Query optimizer
│       ├── benchmark/    # Benchmark framework (C1–C10)
│       ├── datasets/     # Dataset generators
│       ├── visualization/ # Publication-quality plots
│       └── cli.py        # Command-line interface
├── tests/                # 347 unit tests
├── paper/                # LaTeX paper (50+ sections)
├── research/             # Future models survey, audit, scorecard
│   └── future_models/    # 25 model analyses
├── docs/                 # Documentation
├── configs/              # Benchmark configuration
├── scripts/              # Utility scripts
├── results/              # Generated benchmark outputs
├── pyproject.toml
├── CITATION.cff
└── README.md
```

## Architecture

Two engines implement the `DatabaseEngine` ABC:

1. **KnowledgeGraphEngine** — Triple-store baseline (RDF model, SPARQL querying)
2. **SheafDatabaseEngine** — Sheaf-native engine (topological space, presheaf, consistency checking)

### Sheaf Database Key Components

| Component | Description |
|-----------|-------------|
| `FiniteTopologicalSpace` | Open sets of facts grouped by semantic property |
| `Presheaf` / `Sheaf` | Sections over open sets with restriction maps |
| `ConsistencyChecker` | 5 presheaf/sheaf axiom checks |
| `RestrictionGraph` | Directed acyclic graph of open set inclusions |
| `SheafOptimizer` | Query classification (local/semi-local/global) |
| `SheafQueryPlanner` | Restriction-based query execution |
| `GlobalSectionCache` | Cached gluing results |

## Benchmarks

10 contextual workloads (C1–C10):

| ID | Workload | Description |
|----|----------|-------------|
| C1 | Event Reconstruction | Reconstruct facts from open set membership |
| C2 | Entity Neighborhood | Traverse entity-entity adjacencies |
| C3 | High-Arity Lookup | N-ary fact retrieval (arity 3, 5, 8) |
| C4 | High-Arity Join | Multi-relational join over n-ary facts |
| C5 | Temporal Interval | Time-window overlap queries |
| C6 | Temporal Aggregation | Sliding-window count aggregation |
| C7 | Provenance Lineage | Source/method chain traversal |
| C8 | Consistency Checking | Cocycle condition verification |
| C9 | Global Section | Sheaf gluing reconstruction |
| C10 | Mixed Workload | Combined context + temporal + provenance |

## Key Results

- **Insert performance**: O(N) scaling (~54× faster at N=1000 vs baseline)
- **Context queries**: SheafDB faster via restriction maps
- **Consistency**: Native sheaf axiom checking
- **Global sections**: Pairwise overlap gluing

## Dependencies

Runtime (25): numpy, scipy, pandas, pyarrow, duckdb, rdflib, networkx,
matplotlib, rich, typer, orjson, psutil, pydantic, pyyaml

Dev (6): pytest, pytest-cov, hypothesis, mypy, ruff, types-psutil, types-pyyaml

## Publication

See `paper/` for the full LaTeX paper. All figures are auto-generated from benchmark data.

## Citation

```bibtex
@software{sfdb2026,
  title = {Semantic Fact Database (SFDB)},
  version = {0.1.0},
  year = {2026},
  url = {https://github.com/placeholder/semantic-fact-db}
}
```

## License

MIT
