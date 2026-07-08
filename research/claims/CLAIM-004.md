# CLAIM-004: Context-indexed storage avoids join explosion

## Claim
Storing n-ary facts as sheaf sections avoids the reification join overhead required by traditional RDF triple stores.

## Evidence
Complexity analysis in paper Section 3.2 shows reification of an n-ary fact requires 2n+1 triples, producing O(n log n) join overhead for queries. SheafDB stores one section per n-ary fact with O(1) lookup by section ID and O(n) restriction traversal.

## Supporting Experiments
relation_dense benchmark: queries over reified relations (Q6-Q10) show SheafDB 3-10x faster than KG for arity >= 4. Direct linear scaling with arity for SheafDB vs super-linear for KG.

## Supporting Mathematics
Reification in RDF requires 2k+1 triples for a k-ary relation (Angles & Gutierrez 2008). Querying reified relations requires joining across all triples, producing O(k log k) join cost. SheafDB encodes a k-ary fact as a single section with k attribute slots; queries traverse at most O(k) restriction maps.

## Supporting References
- Angles & Gutierrez, "Survey of RDF reification", 2008
- Paper Section 3.2 (N-ary Fact Storage)
- relation_dense benchmark results

## Paper Section
Section 3.2 — N-ary Fact Representation, Section 6.3 — Relation-Dense Benchmarks

## Implementation Modules
- `src/sheaf_db/operations/query.py` — Section-based query execution
- `src/knowledge_graph/kg_operations.py` — Triple-based query execution
- `src/verification/canonical_model.py` — Canonical mapping for reification

## Benchmark Figures
Figure 5: Query latency vs relation arity; Figure 6: Join overhead comparison

## Certainty
MEDIUM

## Risk if Claim Is False
MEDIUM — KG may have other optimizations (property tables, graph partitioning) that partially mitigate reification overhead. The advantage may be theoretical but not practical in all cases.
