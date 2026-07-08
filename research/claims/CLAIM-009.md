# CLAIM-009: Sheaf storage reduces memory for n-ary facts

## Claim
Storing one section per n-ary fact vs 2+k triples for reified facts saves memory for large arity.

## Evidence
Complexity analysis and storage benchmark results show SheafDB uses O(1) storage per fact (one section record) vs O(k) for KG (k+2 triples per k-ary fact). For arity >= 3, SheafDB consistently uses less storage.

## Supporting Experiments
Storage benchmark across varying arity (2-10) shows SheafDB memory grows by ~32 bytes per additional attribute slot; KG grows by ~192 bytes per additional reified triple (3 triples per value). Cross-over at arity 3.

## Supporting Mathematics
Reification: 1 type triple + k value triples + 1 triple per value link = 2k+1 triples for k-ary fact. Each triple has ~96 bytes overhead (3 index entries). SheafDB: 1 section with k attributes + restriction map links = ~64 + 16k bytes.

## Supporting References
- Paper Section 3.2 (Storage Comparison)
- Storage benchmark results
- Angles & Gutierrez 2008 reification analysis

## Paper Section
Section 3.2 — Storage Model, Section 6.5 — Storage Benchmark

## Implementation Modules
- `src/sheaf_db/storage/section_store.py` — Section storage
- `src/knowledge_graph/kg_storage.py` — Triple storage
- `src/results/storage_analysis.py` — Storage analysis

## Benchmark Figures
Figure 10: Storage per fact vs arity; Figure 11: Cumulative storage for N facts

## Certainty
MEDIUM

## Risk if Claim Is False
MEDIUM — restriction map index may partially offset memory savings for small arity or highly connected data. The advantage is asymptotic but real-world overhead depends on implementation.
