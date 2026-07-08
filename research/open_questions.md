# Open Research Questions

## Unsolved Problems

1. **Can sheaf gluing be made incremental?** Currently, gluing recomputes from scratch on every topology change. An incremental algorithm could track minimal delta sets.

2. **Can restriction maps be lazily computed?** Eager storage of all restriction maps is O(n^2) in the number of contexts. A lazy/thunk-based approach could trade recomputation for memory.

3. **Is there a practical distributed sheaf database?** Sheaves are inherently local-to-global — partitioning across nodes should be natural, but consistency and query routing remain open.

4. **Can sheaves handle non-hierarchical/overlapping contexts?** Alexandrov topologies assume a preorder. Real-world contexts often overlap arbitrarily (e.g., tags, facets). A sheaf over a site (Grothendieck topology) may be needed.

5. **How does SheafDB perform at 10^6+ facts?** Current benchmarks use ~10^4 facts. Scalability to million-scale facts is untested; memory and gluing cost could be bottlenecks.

6. **Can SheafDB support SPARQL 1.1 fully?** SPARQL 1.1 includes subqueries, negation, property paths, and aggregates. The sheaf model handles conjunctive queries naturally; non-monotonic features may require extensions.

7. **How to optimize gluing for lattice-structured (vs tree) contexts?** Tree-structured contexts admit O(n) gluing. Lattices introduce multiple inheritance — the current algorithm degrades with join/meet operations.

8. **Can the cost-based optimizer incorporate learned cost models?** Learned cardinality estimation could replace hand-tuned heuristics, but training data and feature engineering for sheaf-specific operators are unexplored.

9. **What is the relationship between sheaf cohomology and query semantics?** Cech cohomology measures obstructions to global sections — this may correspond to inconsistency or incompleteness in query answers.

10. **Can the sheaf model support probabilistic/uncertain facts?** A probabilistic sheaf would assign measures to sections rather than boolean truth values. The gluing condition would need to incorporate measure-theoretic constraints.

## Future Extensions

1. Multi-node distributed sheaf database (horizontal scaling)
2. Incremental gluing with change propagation (eventual consistency)
3. SPARQL 1.1 full compliance (subqueries, aggregates, property paths)
4. Lazy/eager hybrid restriction computation (adaptive)
5. Support for non-Alexandrov topologies (Grothendieck sites)
6. Streaming/event-based fact ingestion (real-time sheaves)
7. Real-world dataset evaluation (Wikidata, DBpedia, ConceptNet)
8. Standard benchmark evaluation (LUBM, SP2Bench, BSBM)
9. Formal verification of theorems (Coq/Lean)
10. GraphQL and Property Graph API support

## Unexpected Observations

- **Constant-factor overhead**: SheafDB latency (~4µs) is consistently ~2x KG (~2µs) across all query types — the sheaf overhead is a near-constant factor, not query-dependent. This suggests the sheaf machinery adds fixed per-query cost independent of query complexity.

- **Memory profiling gap**: All memory metrics show 0 bytes delta in benchmarks — the profiler may not be capturing sheaf-specific allocations, or Python's GC may obscure true memory usage.

- **Empty-result verification**: Consistency benchmark verification passes trivially because the adapter returns empty results — actual cross-engine equivalence checking may be less informative than expected.

- **Cache not exercised**: The 3-level LRU query cache shows 0 hits and 0 misses across all benchmark runs — caching may not be engaged during benchmark execution, or benchmark queries bypass the cache layer.

## Potential Follow-up Papers

1. **"Incremental Sheaf Computation for Dynamic Knowledge Graphs"** — algorithms for sheaf maintenance under insert/delete/update
2. **"Distributed Sheaf Databases: Scaling Restriction Maps"** — partitioning and distributed gluing protocols
3. **"Sheaf Cohomology for Query Answering"** — theoretical connection between Cech cohomology and query semantics
4. **"SheafDB vs Property Graphs: An Empirical Comparison"** — systems-level benchmarking against Neo4j, ArangoDB, etc.
5. **"Lazy Restriction Maps: Trading Space for Time in Sheaf Databases"** — thunk-based restriction with memoization strategies

## Potential PhD Topics

1. **Sheaf-theoretic foundations for contextual knowledge representation** — formal category-theoretic model of contexts, consistency, and translation
2. **Scalable sheaf computation for database systems** — algorithms and data structures for sheaf operations at scale
3. **Category-theoretic query optimization** — using universal properties to derive query plans
4. **Topological methods for data integration** — sheaf cohomology as a measure of data consistency across heterogeneous sources
