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

# Run tests (417 tests; 14 require a live Jena/Virtuoso/GraphDB instance
# and skip otherwise -- see docs/benchmarking.md)
uv run pytest

# Type check
uv run mypy src/

# Lint
uv run ruff check src/
```

### Docker

For reproducibility independent of host Python/OS, build and run the test
suite in a container:

```bash
docker build -t sfdb .
docker run --rm sfdb                          # runs the test suite
docker run --rm sfdb uv run sfdb benchmark     # runs the benchmark suite
```

The image does not include TeX Live (for building `paper/main.pdf`) or the
external Jena/Virtuoso/GraphDB stores (the "External Reference Point"
sections in
`paper/sections/evaluation.tex`), which require their own separately running
server reachable from the container; see `docs/benchmarking.md`.

## CLI Usage

```bash
# Initialize a database
uv run sfdb init

# Run the paper's benchmark suite (all 4 scales: 100, 1000, 10000, 100000 facts)
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
├── tests/                # 417 unit tests
├── paper/                # LaTeX paper
├── research/             # Supporting proofs, notes, literature survey
├── docs/                 # Documentation
├── scripts/              # benchmark runners (lubm_benchmark.py,
│                         # jena/virtuoso/graphdb_reference.py, ...) plus
│                         # generate_tables.py / generate_figures.py, which
│                         # regenerate paper/tables and paper/figures from
│                         # results/*.json
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
   indexes over SQLite, RDF-style reification for n-ary facts). A
   `storage="memory"` configuration runs **KG-mem**, the storage-layer
   control: identical reification and query logic with Python dict
   indexes in place of the SQLite tables, used to separate
   "context-indexing vs reification" from "dicts vs SQLite round-trips"
   in the benchmark.
2. **SheafDatabaseEngine** — context-indexed engine (finite topological
   space over the context poset, stalk index, restriction cache).

The benchmark additionally compares against **rdflib** (a real,
independent, pure-Python RDF library driven via SPARQL) as an external
reference point — see `scripts/rdflib_reference.py`.

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
five query classes, at four scales (100, 1,000, 10,000, 100,000 facts),
against real `KnowledgeGraphEngine` (SQLite and dict-indexed KG-mem
variants) and `SheafDatabaseEngine` instances, with three-way
cross-engine result verification on every query class at every scale.

| Class | Description |
|-------|-------------|
| LOOKUP | Entity-anchored retrieval (subject match) |
| GLOBAL | Unrestricted full-scan queries |
| CONTEXT | Retrieval scoped to a context and its descendants — the query shape the design is named for |
| TEMPORAL (bounded) | Range queries over a fact's temporal envelope, bounded on both ends |
| TEMPORAL (unbounded) | Range queries with a start bound and no end bound |

The same five classes are also run against LUBM (the standard RDF
benchmark workload, `scripts/lubm_benchmark.py`) and against three real
external stores — Apache Jena TDB2, OpenLink Virtuoso, and Ontotext
GraphDB (`scripts/{jena,virtuoso,graphdb}_reference.py`, plus
`scripts/lubm_external_reference.py --store {jena,virtuoso,graphdb}` for
LUBM data against each). See `docs/benchmarking.md` for the full command
reference and `paper/sections/evaluation.tex` for the full methodology
and results.

## Key Results

(See `paper/main.pdf` for the full evaluation; numbers below are from the
reported run and are regenerated by `scripts/generate_tables.py` from
`results/*.json`. KG-mem is the storage-layer control — same
reification/query logic as KG with dict indexes instead of SQLite. All
ratios are "how many times faster SFDB is" unless stated otherwise; a
ratio below 1× means SFDB is slower.)

- **Insert**: SFDB is 1.06×–1.49× faster than KG at every scale measured
  (100 to 100,000 facts).
- **LOOKUP**: SFDB is 20×–32× faster than KG (8.1×–16× against the KG-mem
  control — most of the advantage survives).
- **GLOBAL**: SFDB is 54×–99× faster than KG (19×–39× against KG-mem).
- **CONTEXT**: SFDB is 2.97×–21× faster than KG (1.59×–9.0× against
  KG-mem) — the query class the design is named for, and a query class
  this project's own evaluation once measured incorrectly (see the bug
  note below).
- **TEMPORAL (bounded)**: SFDB is 1.23×–1.66× faster than raw KG, but
  this does **not** survive the storage-layer control — SFDB is
  0.40×–0.89× relative to KG-mem, i.e. measurably slower at most scales.
  Reported as a negative result: the apparent win is a storage-layer
  effect, not a property of context-indexed storage.
- **TEMPORAL (unbounded)**: SFDB is 1.78×–2.17× faster than raw KG;
  against KG-mem it is 0.59×–1.08× (mixed: slower at the smallest scale,
  near parity or faster at larger ones).
- **Memory**: SFDB uses 1.21×–2.71× more resident memory per fact than
  KG, and about 2.0× more than KG-mem — this is the paper's central
  tradeoff, funding the LOOKUP/GLOBAL/CONTEXT advantages above.
- **Against real production stores** (Apache Jena TDB2, OpenLink
  Virtuoso, and Ontotext GraphDB, accessed over SPARQL/HTTP exactly as
  external clients — see `paper/sections/evaluation.tex` §"External
  Reference Points"): SFDB remains faster than all three on LOOKUP
  (2.44×–666× vs. Jena, 3.3×–536× vs. Virtuoso, 1.80×–465× vs. GraphDB),
  GLOBAL (8.8×–432× / 15×–508× / 6.3×–499×), and CONTEXT
  (2.00×–237× / 3.7×–201× / 1.63×–244×) at every scale, but is overtaken
  by all three on TEMPORAL from 10,000 facts onward — at 100,000 facts,
  roughly 6.7× (Jena), 7.1× (Virtuoso), and 6.3× (GraphDB) slower on
  bounded ranges. TEMPORAL is the one query class with a genuine,
  scale-dependent crossover, reproduced independently against three
  unrelated production optimisers; LOOKUP, GLOBAL, and CONTEXT hold as
  clean wins against every one.
- **Standard benchmark workload (LUBM)**: the same five-class benchmark
  run against LUBM-generated university data (up to 97,289 facts)
  reproduces the pattern — SFDB faster on LOOKUP, GLOBAL, and CONTEXT
  against the in-house baselines (CONTEXT up to 332× vs. KG) and,
  separately, against all three external stores with the dataset and
  the engine varied at once (LOOKUP up to 3,004× vs. Jena), with
  TEMPORAL again the one crossover class. This run is also where a real
  performance bug in SFDB's own CONTEXT query resolution was found and
  fixed — CONTEXT latency scaled with total corpus size rather than
  result size until the fix, invisible to every correctness check
  because results were always right, only the amount of work behind
  them was wrong. Every CONTEXT number in the paper was re-measured
  after the fix; see `paper/sections/discussion.tex`'s bug inventory
  (finding ten) for the full account, including the two earlier claims
  retracted as a direct result.
- **Real-world case study** (5,337 genuine Wikidata "position held"
  facts, national heads of state/government — see
  `paper/sections/evaluation.tex` §"Real-World Case Study"): LOOKUP,
  GLOBAL, and CONTEXT all reproduce the synthetic-benchmark advantage
  cleanly (roughly 14×, 100×, and 50× faster than KG respectively).
  TEMPORAL is the one class that lands differently on real data: SFDB
  is faster than *both* KG (roughly 3×) and KG-mem (roughly 1.2×) here,
  a reversal of the synthetic benchmark's own TEMPORAL-vs-KG-mem result
  — direct evidence that TEMPORAL specifically is sensitive to a
  dataset's actual shape, not only to its scale.

## Dependencies

Runtime (14): numpy, scipy, pandas, pyarrow, duckdb, rdflib, networkx,
matplotlib, rich, typer, orjson, psutil, pydantic, pyyaml

Dev (9): pytest, pytest-cov, hypothesis, mypy, ruff, sphinx, sphinx-rtd-theme,
types-psutil, types-pyyaml

## Publication

See `paper/` for the full LaTeX paper. All tables and figures are
auto-generated from the `results/*.json` files produced by the
benchmark scripts (`sfdb benchmark` and `scripts/*.py`) — see
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
