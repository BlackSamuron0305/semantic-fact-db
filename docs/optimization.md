# Optimization Framework

The `src/optimization/` package provides a unified framework for
managing, benchmarking, and analysing all optimisations across both
the SheafDB and KG engines.

## Architecture

```
src/optimization/
  __init__.py          Package exports
  registry.py          OptimizationRegistry — central registry of all 33 modules
  state.py             OptimizationState — per-optimisation mutable state
  manager.py           OptimizationManager — orchestrator, profile loading, hooks
  profile.py           OptimizationProfile + ProfileManager — named presets
  report.py            OptimizationReport — text, JSON, Markdown reports
  ablation.py          AblationStudy — leave-one-out, pairwise, random-subset
  sensitivity.py       SensitivityAnalysis — sweep parameters across ranges
  scalability.py       ScalabilityAnalysis — 9 scaling dimensions
  memory.py            MemoryAnalysis — deep object size estimation
  hotspot.py           HotspotAnalysis + HotspotCollector — instrumentation
  dashboard.py         PerformanceDashboard — HTML + CSV + JSON export
  cli.py               CLI entry point (python -m optimization.cli)
  modules/
    __init__.py
    base.py            BaseOptimization, OptimizationHook
    sheaf/__init__.py  SheafDB-specific module registrations (13 modules)
    kg/__init__.py     KG-specific module registrations (10 modules)
    query/__init__.py  Query-level module registrations (10 modules)
```

## 33 Optimization Modules

### SheafDB (13)
| # | Name | Category | Default | Description |
|---|------|----------|---------|-------------|
| 1 | `sheaf.restriction_cache` | cache | ON | Cache restriction map results |
| 2 | `sheaf.global_section_cache` | cache | ON | Cache computed global sections |
| 3 | `sheaf.neighborhood_index` | index | ON | Entity adjacency for O(1) neighbourhood queries |
| 4 | `sheaf.context_index` | index | ON | Context string -> fact IDs |
| 5 | `sheaf.temporal_index` | index | ON | Year-based temporal index |
| 6 | `sheaf.provenance_index` | index | ON | Source/method provenance index |
| 7 | `sheaf.topology_compression` | storage | OFF | Collapse open sets with identical sections |
| 8 | `sheaf.lazy_restriction` | execution | OFF | Defer restriction until accessed |
| 9 | `sheaf.stalk_prefetch` | execution | OFF | Prefetch likely stalks |
| 10 | `sheaf.section_dedup` | storage | OFF | Deduplicate identical sections |
| 11 | `sheaf.parallel_gluing` | execution | OFF | Parallelise global section computation |
| 12 | `sheaf.context_aware_gluing` | algorithm | OFF | Only glue sections sharing a context |
| 13 | `sheaf.incremental_update` | algorithm | OFF | Incremental updates (no full recompute) |

### Knowledge Graph (10)
| # | Name | Category | Default | Description |
|---|------|----------|---------|-------------|
| 1 | `kg.six_index` | index | OFF | Six-way SPO/POS/OPS/SOP/PSO/OSP indexes |
| 2 | `kg.dictionary_encoding` | storage | ON | String -> integer encoding |
| 3 | `kg.dictionary_cache` | cache | ON | In-memory dictionary lookup cache |
| 4 | `kg.predicate_partitioning` | storage | OFF | Partition triples by predicate |
| 5 | `kg.join_reordering` | algorithm | ON | Reorder hash joins by cardinality |
| 6 | `kg.filter_pushdown` | algorithm | ON | Push filters toward scans |
| 7 | `kg.batch_insert` | execution | ON | Batch inserts into one transaction |
| 8 | `kg.pragma_tuning` | execution | ON | SQLite PRAGMA (WAL, synchronous) |
| 9 | `kg.reification_skip` | execution | ON | Skip unused reification triples |
| 10 | `kg.result_caching` | cache | OFF | Cache query results by normalized text |

### Query-Level (10)
| # | Name | Category | Default | Description |
|---|------|----------|---------|-------------|
| 1 | `query.lru_parsed_cache` | cache | ON | LRU cache of parsed AST |
| 2 | `query.lru_logical_cache` | cache | ON | LRU cache of logical plans |
| 3 | `query.lru_physical_cache` | cache | ON | LRU cache of physical plans |
| 4 | `query.constant_folding` | algorithm | ON | Constant expression evaluation |
| 5 | `query.predicate_pushdown` | algorithm | ON | Move predicates to scans |
| 6 | `query.projection_pushdown` | algorithm | ON | Remove unused columns |
| 7 | `query.dead_operator_removal` | algorithm | ON | Remove no-result operators |
| 8 | `query.logical_simplification` | algorithm | ON | Simplify redundant operators |
| 9 | `query.cost_optimizer` | algorithm | ON | Optimal engine via cost model |
| 10 | `query.result_caching` | cache | OFF | Cache final query results |

## Profiles

| Profile | ON | Description |
|---------|----|-------------|
| `minimal` | 7 | Only essential optimizations for correctness |
| `default` | 22 | All stable optimizations (production sweet spot) |
| `research` | 27 | All stable + research optimizations (paper novelty claims) |
| `max` | 33 | All optimizations including experimental |
| `memory` | 10 | Minimal memory footprint |
| `debug` | 0 | All disabled, maximum instrumentation |

## CLI Usage

```bash
# Show optimization status
python -m optimization.cli report

# List all optimizations
python -m optimization.cli list
python -m optimization.cli list --engine sheaf

# Manage profiles
python -m optimization.cli profile list
python -m optimization.cli profile show research
python -m optimization.cli profile apply default

# Analysis (structural validation with dummy benchmark)
python -m optimization.cli ablation
python -m optimization.cli sensitivity --param cache_size
python -m optimization.cli scalability

# Generate dashboard
python -m optimization.cli dashboard
```

## Programmatic Usage

```python
from optimization import OptimizationManager

mgr = OptimizationManager()
mgr.load_profile("research")
mgr.set("sheaf.parallel_gluing", True)
mgr.set_parameter("sheaf.parallel_gluing", "max_workers", 8)
mgr.activate()

# ... run benchmarks ...

report = mgr.report()
print(report.to_text())
print(report.to_markdown())

# Ablation study
from optimization import AblationStudy
study = AblationStudy(mgr, benchmark_fn)
result = study.run(strategy="leave_one_out")
per_opt = result.per_optimization()
```

## Quality Gates

1. **Every optimization is optional**: Each of the 33 modules can be
   independently enabled/disabled via the manager.
2. **Semantically neutral**: All optimizations preserve query semantics;
   the ablation framework verifies cross-engine equivalence.
3. **Default-on is safe**: The `default` profile (22 ON) includes only
   stable, well-tested optimizations.
4. **Benchmarkable**: The ablation, sensitivity, and scalability
   frameworks auto-generate benchmark configurations.
5. **Reportable**: Every optimization exposes hit counts, hit rates,
   and memory estimates via OptimizationReport.
6. **No circular dependencies**: Dependency chains are tree-structured
   and auto-resolved by the manager.
