# CLAIM-003: Sheaf insertion O(d) amortized

## Claim
SheafDB has lower insertion cost than KnowledgeGraph for deeply nested contexts.

## Evidence
micro_1k benchmark results show SheafDB insertion latency grows with context depth d, not with total fact count N. KnowledgeGraph insertion requires O(log N) index updates regardless of context structure. For deeply nested insertion paths (depth > 5), SheafDB outperforms KG by 2-5x.

## Supporting Experiments
micro_1k benchmark: 1,000 insertions at varying context depths. SheafDB insertion time per fact shows O(d) scaling where d is context depth; KG shows O(log N) scaling independent of depth. Cross-over point at ~depth 5.

## Supporting Mathematics
SheafDB inserts a single section into the section store with O(1) storage and O(d) restriction map updates (one per ancestor context). KG inserts N triples for an N-ary fact, each requiring O(log N) B-tree index update.

## Supporting References
- Paper Section 6 (Benchmarks)
- Paper Section 4.1 (Sheaf Insertion Algorithm)
- micro_1k benchmark results table

## Paper Section
Section 4.1 — Sheaf Insertion, Section 6.2 — Micro-benchmarks

## Implementation Modules
- `src/sheaf_db/operations/insert.py` — Section insertion with restriction propagation
- `src/sheaf_db/storage/section_store.py` — Section store backend
- `src/shared/models.py` — Fact and section data models

## Benchmark Figures
Figure 3: Insertion latency vs context depth; Figure 4: Insertion throughput comparison

## Certainty
MEDIUM

## Risk if Claim Is False
MEDIUM — core performance claim needs larger-scale validation. Current benchmarks only tested up to 1K facts; behavior at 10^5+ may differ. Restriction map index overhead may reduce gains for shallow contexts.
