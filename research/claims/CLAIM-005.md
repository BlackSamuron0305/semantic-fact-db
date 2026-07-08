# CLAIM-005: SheafDB preferred for contextual queries

## Claim
SheafDB outperforms KnowledgeGraph when queries are scoped to a context sub-hierarchy.

## Evidence
Benchmark results from deep_context and mixed benchmarks show SheafDB query latency grows with sub-hierarchy size rather than total database size. KG must filter across all triples regardless of context scope. SheafDB shows 5-20x speedup for queries targeting narrow sub-contexts in large databases.

## Supporting Experiments
deep_context benchmark: queries targeting specific branches of 10-level context hierarchy. SheafDB latency = O(subtree_size); KG latency = O(log N) for index + O(filter) for context matching. For narrow queries (subtree < 1% of total), SheafDB is faster.

## Supporting Mathematics
Sheaf section store is indexed by context ID, enabling direct subtree traversal via context poset. Restriction maps provide pre-computed context narrowing. KG triple store requires full index scan + subject/predicate/object matching, then post-filter by context.

## Supporting References
- Paper Section 6.4 (Context-Heavy Benchmarks)
- deep_context benchmark results table

## Paper Section
Section 6.4 — deep_context Benchmark Results

## Implementation Modules
- `src/sheaf_db/operations/query.py` — Context-scoped query execution
- `src/sheaf_db/context_poset.py` — Sub-hierarchy traversal
- `src/knowledge_graph/kg_operations.py` — Context filtering in KG

## Benchmark Figures
Figure 7: Query latency vs context scope size; Figure 8: deep_context results

## Certainty
HIGH

## Risk if Claim Is False
HIGH — current benchmarks may not clearly demonstrate this advantage if KG is optimized with context indexes. If false, the primary use case advantage of SheafDB is undermined.
