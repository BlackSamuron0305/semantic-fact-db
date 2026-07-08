# CLAIM-006: KG preferred for non-contextual dense graphs

## Claim
KnowledgeGraph triple indexes provide faster access than SheafDB for flat, highly interconnected data with minimal context structure.

## Evidence
Complexity analysis and preliminary benchmarks show KG's B-tree indexes on each triple component (subject, predicate, object) provide O(log N) lookup for any graph traversal pattern. SheafDB must traverse restriction maps even for flat data, adding overhead.

## Supporting Experiments
relation_dense benchmark queries Q1-Q5 (non-contextual, highly connected): KG matches or slightly outperforms SheafDB for dense subgraph traversal. Gap narrows with caching but KG remains faster for unfiltered graph queries.

## Supporting Mathematics
KG triple store: 3 B-tree indexes provide O(log N) access by any component. SheafDB: section store lookup is O(1) by section ID, but graph traversal requires loading restriction maps and filtering sections, adding constant-factor overhead.

## Supporting References
- Paper Section 6.3 (relation_dense results)
- Complexity analysis in Section 3.3

## Paper Section
Section 3.3 — Comparative Complexity Analysis, Section 6.3 — relation_dense

## Implementation Modules
- `src/knowledge_graph/kg_storage.py` — Triple index structures
- `src/sheaf_db/storage/section_store.py` — Section storage
- `src/knowledge_graph/kg_operations.py` — Graph traversal operations

## Benchmark Figures
Figure 9: Flat query performance comparison; relation_dense Q1-Q5 results

## Certainty
MEDIUM

## Risk if Claim Is False
MEDIUM — if KG does not outperform SheafDB in its own domain, the trade-off narrative of the paper is weakened. Needs an explicit benchmark designed to demonstrate this.
