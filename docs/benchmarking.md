# Benchmarking Methodology

> **Corrected 2026-08-16.** This document previously described a
> different framework than what is implemented: a `python -m
> sfdb.benchmark.cli` CLI that does not exist (the real entry point is
> `uv run sfdb benchmark`), Apache Jena TDB2 / Blazegraph / Neo4j listed
> as "supported (optional)" engines when only rdflib has a working
> adapter (Blazegraph and Neo4j raise `NotImplementedError` on
> construction), a Q1–Q15 workload taxonomy that does not match the five
> query classes the paper actually measures, and DBpedia/YAGO/Wikidata
> dataset loaders that do not exist (only a synthetic generator and a
> LUBM loader do). Rewritten below to describe
> `sfdb.benchmark.paper_suite`, the actual single source of truth for
> the paper's numbers.

## Overview

`sfdb.benchmark.paper_suite` is the benchmark suite that produces every
number in the paper (`paper/main.pdf`). It measures insert throughput
and five query classes against three engine configurations, at four
scales, with three-way cross-engine result verification on every
class at every scale.

## Engines

1. **KnowledgeGraph** (`sfdb.kg.engine.KnowledgeGraphEngine`) — SQLite-backed
   reified triple store; the paper's baseline.
2. **KnowledgeGraphMem** (`KnowledgeGraphEngine(storage="memory")`) — the
   storage-layer control: identical reification and query logic to
   KnowledgeGraph, with Python dicts in place of the SQLite tables. Exists
   to separate "avoiding reification" from "avoiding SQLite round trips."
   Runs no write-through persistence, so its insert numbers are reported
   for completeness only, not as a comparison point.
3. **SheafDatabase** (`sfdb.sheaf.engine.SheafDatabaseEngine`) — the
   context-indexed design under study.

`sfdb.benchmark.engine_adapter.RdflibEngineAdapter` additionally wraps
`rdflib` (a real, independent, pure-Python RDF library) as an external
reference point, driven via SPARQL text rather than the typed `Query`
interface — see `scripts/rdflib_reference.py`.

Three further adapters wrap genuine, disk-backed production RDF stores,
each accessed exactly as an external client would — over HTTP via the
standard SPARQL 1.1 protocol, with no internal API access:

- **`JenaTDB2EngineAdapter`** wraps a real Apache Jena TDB2 store via a
  Fuseki HTTP server — see `scripts/jena_reference.py` and the setup
  instructions below.
- **`VirtuosoEngineAdapter`** wraps a real OpenLink Virtuoso
  (open-source edition) store, accessed via HTTP Digest-authenticated
  SPARQL Update for inserts and plain SPARQL Query for reads — see
  `scripts/virtuoso_reference.py` and the setup instructions below.
  Virtuoso requires every `INSERT DATA` triple to be wrapped in an
  explicit named graph (unlike Jena, which accepts unqualified
  default-graph triples), and its SPARQL compiler hits a
  parse-time memory limit on very large `INSERT DATA` blocks, so the
  adapter batches inserts at 200 facts rather than the 2,000 used for
  Jena. Reads use Virtuoso's `default-graph-uri` HTTP parameter so the
  same, unmodified SPARQL query text used for Jena and rdflib also works
  against the named graph — no query text is forked per engine.
- **`GraphDBEngineAdapter`** wraps a real Ontotext GraphDB (free
  edition) store — see `scripts/graphdb_reference.py` and the setup
  instructions below. GraphDB needs neither authentication nor a named
  graph for inserts (closer in that respect to Jena than to Virtuoso),
  and its plain-literal relational comparisons already behave correctly
  under the SPARQL 1.1 simple-literal ordering extension (unlike
  Virtuoso), so no engine-specific query workaround was needed. The
  adapter auto-creates its `sfdb` repository via GraphDB's REST API on
  first use, so no manual repository-setup step is required beyond
  starting the container.

`BlazegraphEngineAdapter` and `Neo4jEngineAdapter` are scaffolds that
raise `NotImplementedError` on construction; they are not part of any
reported result.

### Setting up Apache Jena TDB2

Requires a Java 17+ runtime.

```bash
curl -LO https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-6.2.0.zip
unzip apache-jena-fuseki-6.2.0.zip && cd apache-jena-fuseki-6.2.0
java -jar fuseki-server.jar --loc=./tdb2data --update --port 3030 /sfdb &

# From the repository root:
uv run python scripts/jena_reference.py
```

### Setting up OpenLink Virtuoso

The simplest route is the official Docker image:

```bash
docker run -d --name virtuoso-sfdb -p 8890:8890 -p 1111:1111 \
    -e DBA_PASSWORD=sfdb_bench_2026 \
    openlink/virtuoso-opensource-7:latest

# From the repository root:
uv run python scripts/virtuoso_reference.py
```

### Setting up Ontotext GraphDB

The simplest route is the official Docker image:

```bash
docker run -d --name graphdb-sfdb -p 7200:7200 ontotext/graphdb:10.7.3

# From the repository root:
uv run python scripts/graphdb_reference.py
```

## Query Classes

| Class | Description |
|-------|-------------|
| LOOKUP | Entity-anchored retrieval (subject match) |
| GLOBAL | Unrestricted full-scan queries |
| CONTEXT | Retrieval scoped to a context and its descendants — the query shape the design is named for |
| TEMPORAL (bounded) | Range queries over a fact's temporal envelope, bounded on both ends |
| TEMPORAL (unbounded) | Range queries with a start bound and no end bound |

## Scales

`100`, `1,000`, `10,000`, `100,000` facts (`PAPER_SCALES` in
`paper_suite.py`). Each latency figure is the arithmetic mean of ten
timed runs following two warm-up iterations.

## Datasets

### Synthetic

`sfdb.datasets.synthetic.generate_facts`, configured by `SyntheticConfig`:
controllable entity/relation counts, arity range (default 3–8), context
depth and branching (default depth 3, branching 2), a Zipf-like entity
skew (default α = 1.2), and a fraction of facts given a temporal envelope
(default 40%). Seeded (default seed 42) for reproducibility.

### LUBM

`sfdb.datasets.lubm` implements a loader for the Lehigh University
Benchmark ontology, the standard benchmark workload for RDF stores. It
is scaled by university count rather than fact count; `LUBMConfig`
takes `num_universities`, and `takesCourse`/`teacherOf` facts carry a
one-semester temporal envelope (added so the loader exercises TEMPORAL
too — the original ontology loader had no temporal data at all).

Two scripts run it:

```bash
uv run python scripts/lubm_benchmark.py                       # vs. the three in-house engines
uv run python scripts/lubm_external_reference.py --store jena # vs. a real external store
#   (or --store virtuoso, --store graphdb)
```

`lubm_benchmark.py` reproduces the paper's usual five-class benchmark
at four university-count scales (1, 3, 26, 265 — chosen to land close
to the paper's usual 100/1,000/10,000/100,000 fact-count scales)
against KnowledgeGraph, KnowledgeGraphMem, and SheafDatabase.
`lubm_external_reference.py` runs the identical LUBM data and query
anchors against a real, disk-backed Jena/Virtuoso/GraphDB instance,
varying both the dataset and the comparison engine at once — the one
axis-combination no other comparison in this paper tests. See
`paper/sections/evaluation.tex`'s "Standard Benchmark Workload: LUBM"
and "LUBM Against External Stores" subsections for the results,
including the CONTEXT performance bug LUBM's topology surfaced (a
many-large-mutually-unrelated-top-level-contexts shape none of the
other datasets exercise) and its fix.

### Wikidata (real-world case study)

`sfdb.datasets.wikidata_case_study` loads a genuine, organic dataset —
national head-of-state/government office-holders sourced from
Wikidata's public SPARQL endpoint — rather than anything this project's
authors constructed to fit the design. Each fact is a real "position
held" (P39) statement with its P580/P582 start/end date qualifiers
where recorded: a genuine instance of the reification problem the paper
opens with (who held what office, in which country, when), not a
synthetic imitation of one.

The loader never queries Wikidata live; it reads a cached snapshot at
`data/wikidata_case_study_raw.json`, built by
`scripts/fetch_wikidata_case_study.py`, so benchmark results stay
reproducible even if Wikidata's live data changes later. Re-fetching is
a separate, explicit step:

```bash
uv run python scripts/fetch_wikidata_case_study.py   # refreshes the snapshot (optional)
uv run python scripts/wikidata_case_study_benchmark.py
```

See `paper/sections/evaluation.tex`'s real-world case study section for
the results and `scripts/fetch_wikidata_case_study.py`'s module
docstring for exactly how the position/office sample was constructed
(and the two dead ends — server-side query cost, sample skew — that
shaped the final approach).

No DBpedia or YAGO loader exists in this codebase.

## Statistical Analysis

For each metric, `sfdb.benchmark.statistics.compute_statistics` reports:
mean, median, variance, standard deviation, P50/P95/P99 percentiles, a
normal-approximation 95% confidence interval, and a bootstrap 95%
confidence interval (10,000 resamples). Query latency tables in the
paper report the mean and the normal-approximation 95% CI half-width.

## Correctness Verification

Before recording performance for a query class at a scale,
`sfdb.benchmark.verification.verify_equivalence` checks that all three
engines produce identical canonical result sets (order-independent,
type-preserving). A divergence is logged and the row is flagged as
unverified rather than silently included; every row reported in the
paper passed this check.

## Reproducibility

Each benchmark run's manifest (`sfdb.benchmark.reproducibility.ReproducibilityRecord`)
records: Python version, `uv.lock` hash, git commit hash, CPU model and
core count, total memory, operating system, random seed, and a checksum
of the generated dataset at every scale. Written to
`results/paper_suite_reproducibility.json` and turned into LaTeX macros
by `scripts/generate_tables.py`.

## Limitations

- Blazegraph and Neo4j adapters are stubs; only KG, KG-mem, SFDB,
  rdflib, Jena TDB2, Virtuoso, and GraphDB are implemented.
- The rdflib reference point is capped at 10,000 facts — its SPARQL
  engine does not sustain the scan-shaped classes at 100,000 facts in
  reasonable benchmark time. Jena, Virtuoso, and GraphDB are each run at
  all four
  paper scales, up to 100,000 facts.
- Three production RDF stores (Jena TDB2, Virtuoso, GraphDB) have been
  compared, all showing the same LOOKUP/GLOBAL/CONTEXT-vs-TEMPORAL
  crossover reported in `paper/sections/evaluation.tex`, reproduced
  again with LUBM data against all three stores; a fourth or fifth store
  (e.g. Blazegraph, Stardog) would strengthen the generalisation claim
  further but has not been tried.
- The Wikidata real-world case study (`sfdb.datasets.wikidata_case_study`)
  was benchmarked only against the three in-house engines (KG, KG-mem,
  SFDB), not against the three external production stores.
- Synthetic datasets, beyond the Wikidata case study and LUBM, may not
  capture the full range of real-world data distributions. LUBM has now
  been run both against the in-house engines and against all three
  external stores (`scripts/lubm_external_reference.py`), at four
  university-count scales; BSBM and WatDiv have not been tried at all,
  nor has LUBM at the much larger scales published LUBM results use —
  see `paper/sections/future_work.tex`.

## Usage

```bash
# Run the full paper suite (all scales, all query classes, three engines)
uv run sfdb benchmark

# Run a single scale for a quick check
uv run sfdb benchmark --size tiny --runs 3 --warm-up 1

# External rdflib reference point
uv run python scripts/rdflib_reference.py

# External production-store reference points (each requires a separately
# running server/container -- see the setup instructions above)
uv run python scripts/jena_reference.py
uv run python scripts/virtuoso_reference.py
uv run python scripts/graphdb_reference.py

# Real-world case study (reads a cached snapshot, no live query needed)
uv run python scripts/wikidata_case_study_benchmark.py

# LUBM standard benchmark workload, vs. in-house engines and vs. each external store
uv run python scripts/lubm_benchmark.py
uv run python scripts/lubm_external_reference.py --store jena
uv run python scripts/lubm_external_reference.py --store virtuoso
uv run python scripts/lubm_external_reference.py --store graphdb

# Regenerate paper tables/figures from the latest results
uv run python scripts/generate_tables.py
uv run python scripts/generate_figures.py

# Benchmark dashboard (HTML)
uv run sfdb dashboard
```

See `paper/sections/evaluation.tex` for the full methodology and results,
and `paper/sections/artifact.tex` for the complete reproduction command
sequence.
