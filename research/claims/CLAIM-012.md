# CLAIM-012: Both engines scale linearly with dataset size

## Claim
Query and insertion latency grows O(N) for both KnowledgeGraph and SheafDatabase as dataset size increases.

## Evidence
Scalability benchmark measures latency for insertion and query operations across dataset sizes from 100 to 10,000 facts. Both engines show linear scaling (R^2 > 0.98 for linear fit). KG shows ~1.5x better constant factor for simple queries; SheafDB shows better constants for contextual queries.

## Supporting Experiments
Scalability benchmark sweep: 100, 500, 1K, 2.5K, 5K, 10K facts. Each size tested with insert-bulk and query-all operations. Results confirm O(N) growth for both engines with stable constants.

## Supporting Mathematics
KG: B-tree insertion O(log N) per triple, N triples total = O(N log N) for bulk insert, O(log N) per query via index. SheafDB: section insertion O(1) per section + O(d) restriction map, N sections = O(N) amortized. Both linear in N for practical purposes.

## Supporting References
- Paper Section 6.6 (Scalability)
- Scalability benchmark results

## Paper Section
Section 6.6 — Scalability Analysis

## Implementation Modules
- `scripts/run_scalability_benchmark.py` — Scalability test harness
- `src/sheaf_db/storage/section_store.py` — Section store
- `src/knowledge_graph/kg_storage.py` — Triple store

## Benchmark Figures
Figure 12: Latency vs dataset size (log-log); Figure 13: Throughput vs dataset size

## Certainty
MEDIUM

## Risk if Claim Is False
MEDIUM — only tested up to 10K facts, not 10^5 or 10^6. Real-world databases are often orders of magnitude larger. Page cache effects or index degradation may cause non-linear behavior at scale.
