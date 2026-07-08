# Benchmarking Methodology

## Overview

The Semantic Fact DB benchmarking framework provides a comprehensive,
reproducible evaluation infrastructure for comparing multiple graph
query engines on identical workloads.

## Supported Engines

1. **KnowledgeGraph** — Native triple-store with SPARQL-like query support
2. **SheafDatabase** — Sheaf-theoretic semantic database
3. **Apache Jena TDB2** — (optional) Standard RDF store
4. **Blazegraph** — (optional) High-performance graph database
5. **Neo4j** — (optional) Labeled property graph database

All engines execute identical canonical queries expressed in the common
query language.

## Benchmark Modes

| Mode | Description |
|------|-------------|
| Micro | Individual query-level latency/memory benchmarks |
| Macro | End-to-end workflow simulation |
| Stress | High-concurrency / large-data stress tests |
| Scalability | Latency vs. dataset size scaling |
| Consistency | Cross-engine result equivalence |
| Storage | Storage efficiency and index size |
| Import | Bulk load performance |
| Export | Serialization throughput |

## Cache Modes

- **Cold cache**: 10 runs, fresh state each run
- **Warm cache**: 50 runs, cached state

Outliers are discarded only when statistically justified (Grubbs' test).

## Datasets

### Synthetic

Configurable generator producing facts with controlled properties:

| Parameter | Values |
|-----------|--------|
| Entities | 10–100,000 |
| Relations | 5–500 |
| Facts | 100–1,000,000 |
| Arity | 1–10 |
| Context depth | 1–10 |

### External

- **LUBM**: Lehigh University Benchmark (university ontology)
- **DBpedia**: Subset of the DBpedia knowledge graph
- **YAGO**: Subset of the YAGO ontology
- **Wikidata**: Subset of Wikidata

Deterministic generation with fixed seeds.

## Query Workloads (Q1–Q15)

| ID | Name | Category |
|----|------|----------|
| Q1 | Simple Lookup | Lookup |
| Q2 | Entity Neighborhood | Walk |
| Q3 | Two Hop Traversal | Walk |
| Q4 | Four Hop Traversal | Walk |
| Q5 | Temporal Filtering | Filter |
| Q6 | Context Filtering | Filter |
| Q7 | Provenance Filtering | Filter |
| Q8 | Aggregation | Aggregate |
| Q9 | Mixed Query | Mixed |
| Q10 | Global Semantic Reconstruction | Reconstruction |
| Q11 | Insertion | Write |
| Q12 | Update | Write |
| Q13 | Deletion | Write |
| Q14 | Import | IO |
| Q15 | Export | IO |

## Metrics

| Metric | Unit | Collection |
|--------|------|------------|
| Insert latency | ms | Per-insert timer |
| Query latency | ms | Per-query timer |
| Planning latency | ms | Optimizer timer |
| Execution latency | ms | Engine timer |
| Memory (RSS) | bytes | psutil |
| CPU | % | psutil |
| Storage | bytes | File system |
| Index size | bytes | Engine report |
| Import speed | facts/s | Timer + count |
| Export speed | triples/s | Timer + count |
| Cache hit rate | % | Cache profiler |

## Statistical Analysis

For each metric we collect:
- Mean, median, variance, standard deviation
- P50, P95, P99 percentiles
- 95% confidence intervals (normal approximation)
- Bootstrap confidence intervals (10,000 resamples)
- Speedup ratios

## Correctness Verification

Before recording performance, every benchmark verifies that all engines
produce identical `CanonicalResult` output for each query. Benchmarks
are rejected if results differ.

## Reproducibility

Each benchmark run automatically records:
- Python version
- uv lock hash
- Git commit hash
- CPU model and count
- Total memory
- Operating system
- Random seed
- Dataset checksum
- Engine versions
- Timestamp

## Limitations

- External engines (Jena, Blazegraph, Neo4j) require separate installation
- Warm-cache benchmarks may be affected by OS-level caching
- Microbenchmarks may not reflect production workload patterns
- Synthetic datasets may not capture real-world data distributions

## Usage

```bash
# Run default benchmark
python -m sfdb.benchmark.cli benchmark

# Run with all engines
python -m sfdb.benchmark.cli benchmark --engines KnowledgeGraph SheafDatabase

# Run scalability test
python -m sfdb.benchmark.cli benchmark-scalability

# Run consistency check
python -m sfdb.benchmark.cli benchmark-consistency

# Generate visualizations
python -m sfdb.benchmark.cli benchmark --no-visualize
```
