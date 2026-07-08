# Novelty Matrix for SheafDB

## Summary

**What is genuinely novel:**

1. Complete implementation of a sheaf-based database system (presheaf + sheaf condition + restriction maps + gluing) as a working Python codebase with SQLite persistence, indexes, query planning, and benchmark infrastructure. Prior work has proposed sheaf theory for databases theoretically (Patterson 2022) but no complete implementation exists.
2. The specific **cross-engine semantic equivalence mapping** between KG (reified triples) and sheaf (context-indexed sections) with formal injectivity claims and a verification framework that confirms both engines produce identical canonical results.
3. The **local/semi-local/global query classification** over a sheaf with cost-based optimizer choosing between KG and sheaf execution paths — this is a novel query processing architecture not described in prior literature.
4. **Stalk-based query acceleration** as a concrete implementation pattern (pre-computed stalks as persisted direct limits, not computed on the fly).

**What is NOT novel:**

1. The mathematical foundations (sheaf theory, presheaves, restriction maps, gluing) are textbook category theory (Mac Lane & Moerdijk 1992).
2. N-ary fact storage has been done in RDF-star, hypergraphs, property graphs (Neo4j), and named graphs.
3. Context/scope-based data organization is known in RDF named graphs, multi-database systems, and versioned graphs.
4. LRU caches, cost-based optimization, and benchmark frameworks are standard database engineering.
5. Finite topological spaces and Alexandrov topology are well-known mathematics.

**Key risks for reviewers:** The sheaf condition (locality + gluing) is mathematically elegant but the current implementation's gluing algorithm is O(k·m) and trivial — it checks pairwise equality on overlaps. This is not a novel algorithm; it is a direct implementation of the definition. The "sheaf" is a presheaf where gluing is checked at query time (not enforced at insert time), which weakens the mathematical guarantees. The context poset is a simple prefix tree, which is far simpler than the general poset structures in sheaf theory.

---

## Feature-by-Feature Analysis

### 1. Sheaf-theoretic data model (facts as sections over a poset)

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Facts as sheaf sections | Mac Lane & Moerdijk (1992) | Sections over open sets are data elements | Set-valued functor | Restriction maps | Category theory | Full | N/A | Theoretical only | Core data model | Complete overlap with textbook sheaf theory | **KNOWN** |
| | Patterson (2022) | Sheaf theory in database theory | Functorial data model | Functorial query | Category theory | None | N/A | No implementation | Direct precursor | High — same mathematical framework | **KNOWN-NOT-IMPLEMENTED** |
| | Robinson (2020) | Sheaves for data fusion | Consistency sheaves | Local-global consistency | Algebraic topology | MATLAB | Small | Focus on fusion, not query | Similar math, different application | Medium — different application domain | **KNOWN-NOT-IMPLEMENTED** |

### 2. Finite topological space for contexts

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Finite topological spaces | Alexandrov (1937) | Finite spaces = preorders | Minimal open sets | Specialization order | Topology | None | N/A | No computational model | Core topological foundation | Complete — standard math | **KNOWN** |
| | Carlsson (2009) TDA | Topology for data analysis | Point clouds | Persistent homology | Algebraic topology | Various (GUDHI, etc.) | Yes | Analytical, not storage | Different application | Low — different data types | **KNOWN** |
| | Formal Concept Analysis (Ganter & Wille 1999) | Lattice of concepts | Concept lattice | Attribute exploration | Order theory | Various | Yes | No query model | Similar structure (poset) | Medium — same algebraic structure | **KNOWN** |

### 3. Presheaf with restriction maps

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Presheaf functor | Mac Lane & Moerdijk (1992) | Contravariant functor to Set | Functorial assignment | Natural transformations | Category theory | None | N/A | No computational semantics | Exact implementation | Complete — standard definition | **KNOWN** |
| Restriction maps | Standard sheaf theory | ρ_{V,U}: F(V) → F(U) for U ⊆ V | Map between section sets | Filter by subset | Presheaf axioms | None | N/A | — | Exact implementation | Complete | **KNOWN** |

### 4. Sheaf gluing for global reconstruction

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sheaf gluing | Mac Lane & Moerdijk (1992) | Compatible local sections → unique global section | Sheaf condition | Existence/uniqueness | Sheaf theory | None | N/A | Theoretical | Implemented as pairwise overlap check | Complete — standard condition | **KNOWN** |
| Gluing algorithm | SheafDB | O(k·m) pairwise overlap agreement check | Dict of sections | Linear scan | Set equality | Python | Yes | O(k·m), not optimized | This implementation | Only implementation | **KNOWN** (trivial algorithm) |

**Update (July 2026):** The gluing algorithm has been redesigned to implement genuine partial-fact merging. Local sections from different contexts can carry partial information (different attributes, temporal bounds, provenance), and gluing merges compatible sections by taking the union of their fields. This is a non-trivial sheaf-theoretic operation: it checks compatibility on shared fields, merges attributes via union, takes max confidence, and intersects temporal intervals. The algorithm is O(N·K) where N = total sections and K = avg open sets per fact, and it produces a unique global section when compatibility holds. This addresses the reviewer concern that gluing was "just equality checking."

### 5. Context poset (prefix-based partial order)

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Context hierarchy | RDF Named Graphs (Carroll et al. 2005) | Graphs named by URI | Named graph store | Graph-level operations | Set theory | Jena, RDF4J | Yes | Flat names, no hierarchy | Named graphs are flat contexts | Medium — similar but SheafDB adds hierarchy | **KNOWN** |
| Prefix poset | Trie data structure | Prefix-based partial order | Tree | Prefix traversal | Order theory | Various | Yes | Only tree-structured | Direct implementation | Complete — trivial data structure | **KNOWN** |
| Versioned graphs | Git, Delta encoding | Version DAG | Snapshot store | Diff/patch | DAG theory | Git | Yes | — | Versioning uses same poset structure | Low — different purpose | **KNOWN** |

### 6. Canonical model for cross-engine mapping

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Canonical data model | Universal relation (Ullman 1982) | Single schema for heterogeneous data | Common schema | View-based | Relational theory | Various | Yes | Impractical for complex domains | Same concept | Complete — standard approach | **KNOWN** |
| Bidirectional mapping | Lenses (Foster et al. 2007) | Bidirectional transformations | Put/Get | View update | Category theory | boomerang, etc. | Yes | Complex composition | Similar bidirectional concept | Medium — differs in implementation | **KNOWN** |
| Cross-engine mapping | SheafDB | KG ↔ Canonical ↔ Sheaf | CanonicalFact | Injective mapping | Set theory | Python | Yes | Only two engines | This specific mapping | Not in prior work | **NOVEL** |

This is one of the stronger novelty claims: the specific bidirectional mapping between reified RDF triples and sheaf sections, with formal injectivity proof.

### 7. Cross-engine query equivalence

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Query equivalence | Relational completeness (Codd 1970) | Equivalence of query languages | N/A | Relational algebra | Relational theory | None | No | Relational only | Query equivalence across KG and sheaf | Low — different foundation | **KNOWN** |
| Verification framework | SheafDB | Both engines must produce identical canonical results | N/A | Normalized row comparison | Equality | Python | Yes | Only row-level, not semantic | This implementation | Not in prior work | **RESEARCH-PROTOTYPE** |

The verification framework is a research prototype — no prior work verifies KG vs sheaf query equivalence. However, the verification is brute-force row comparison, which is trivial.

### 8. N-ary fact storage (vs triple decomposition)

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| N-ary relations | Entity-Relationship model (Chen 1976) | N-ary relationships | ER diagram | Relational algebra | Set theory | SQL | Yes | Requires normalization | Same concept | Complete — standard data modeling | **KNOWN** |
| | RDF-star (Hartig et al. 2017) | Reification without blank nodes | Embedded triples | SPARQL-star | N/A | Various | Yes | Complex semantics | Similar — n-ary RDF | High — same problem, different solution | **KNOWN** |
| | Property graphs (Angles 2017) | Edges with key-value properties | Adjacency list | Graph traversal | Graph theory | Neo4j | Yes | Binary edges only | Different model | Low — property vs n-ary | **KNOWN-COMMERCIAL** |
| N-ary direct storage | SheafDB | SemanticFact with tuple of objects | Tuple store | Section retrieval | N/A | Python | Yes | Only structured objects | This implementation | — | **KNOWN** |

**Risk:** A reviewer will note that storing n-ary facts directly is not novel. RDF-star, property graphs (with edge attributes), hypergraphs, and ER models all support n-ary or near-n-ary relationships. The specific representation via section objects is different but not fundamentally new.

### 9. Context-indexed section storage

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Context/scoped storage | Named graphs (Carroll 2005) | RDF graphs with names | Quad store | Graph-level SPARQL | Set theory | Jena, etc. | Yes | Flat contexts | SheafDB has hierarchical contexts | Medium — hierarchy is the difference | **KNOWN** |
| Multi-dimensional indexing | Bitmap indexes, R-trees | Composite key indexes | Inverted index | Range scan | Data structures | Various | Yes | Index maintenance | Similar but specific to contexts | Low — different data structures | **KNOWN** |
| Context-indexed sections | SheafDB | Context → fact ID mapping | Dict | O(1) context lookup | N/A | Python | Yes | Simple dict | This index | Only this specific index | **KNOWN** |

### 10. Stalk-based query model

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Stalk as direct limit | Mac Lane & Moerdijk (1992) | Direct limit over neighborhoods | Germ of sections | Local equality | Category theory | None | N/A | Theoretical | Implemented as pre-computed stalk | Complete — standard construction | **KNOWN** |
| Stalk-based lookup | SheafDB | Pre-computed stalks for direct fact access | Stalk index | O(1) stalk lookup | N/A | Python | Yes | Stalks are fact-level, not aggregated | This implementation | Not in prior systems | **KNOWN-NOT-IMPLEMENTED** |

**Note:** The stalk construction is standard mathematics. The implementation as a lookup index is novel only in the sense that no prior database system implements stalks. However, any entity-indexed fact lookup is functionally identical.

### 11. Global section cache

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Query result cache | All major databases | Cache query results | Key-value | Cache hit/miss | N/A | Various | Yes | Invalidation | Standard LRU cache | Complete — standard approach | **KNOWN-COMMERCIAL** |

**Risk:** A reviewer will note this is a standard LRU cache with no novel features. The three-level structure (parsed→logical→physical) is a standard multi-level cache architecture.

### 12. Consistency checking (locality, gluing, functoriality)

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Sheaf consistency | Sheaf theory | Check sheaf axioms hold | N/A | Verification | Category theory | None | N/A | Theoretical | Automated consistency checks | Complete — math is standard | **KNOWN-NOT-IMPLEMENTED** |
| | Database integrity constraints | Referential integrity, constraints | Constraint validation | Validation | Logic | SQL, etc. | Yes | Only relational | Similar concept but via sheaf axioms | Low — different mechanism | **KNOWN-COMMERCIAL** |
| ConsistencyChecker | SheafDB | Automated sheaf axiom verification | Section analysis | 5 diagnostic checks | Sheaf theory | Python | Yes | Only checks, does not enforce | This implementation | No prior implementation found | **RESEARCH-PROTOTYPE** |

The automated consistency checker (check_locality, check_gluing, check_restriction_composition, etc.) is genuinely new as an implementation — no prior system automatically verifies sheaf axioms.

### 13. Benchmark framework with 5 engine adapters

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RDF benchmarks | LUBM (Guo 2005), SP2Bench, WatDiv | Standardized RDF benchmarks | N/A | SPARQL | N/A | Java, etc. | Yes | Only SPARQL | SheafDB extends with sheaf engines | Low — different workload | **KNOWN** |
| Multi-engine benchmarks | GDBB (2023), LDBC | Compare graph databases | N/A | Various | N/A | Various | Yes | Existing engines only | SheafDB includes sheaf engine | Medium — adds novel engine | **KNOWN** |
| SheafDB benchmark | SheafDB | 15 query types × 5 engines | N/A | Canonical result comparison | N/A | Python | Yes | Only 2 of 5 engines work | This framework | — | **KNOWN** |

**Note:** The Jena, Blazegraph, and Neo4j adapters are stubs (no working implementation). Only KG and Sheaf adapters are functional. This significantly weakens the "5 engine" claim.

### 14. Cost-based query optimizer between KG and sheaf paths

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cost-based optimization | System R (Selinger 1979) | Cardinality estimation + cost formulas | N/A | Optimal plan selection | Statistics | DB2, Oracle, PostgreSQL | Yes | Requires accurate statistics | Standard cost-based optimizer | Complete — standard approach | **KNOWN-COMMERCIAL** |
| Cross-model optimization | Polystores, BigDAWG | Query across heterogeneous engines | Multi-model | Federated query | N/A | Various | Yes | Schema mapping | SheafDB specifically compares KG vs sheaf | Medium — different scope | **KNOWN-RESEARCH** |
| KG/Sheaf optimizer | SheafDB | Estimate cost on both paths, pick best | N/A | Plan selection | Heuristic cost formulas | Python | Yes | Heuristic, not data-driven | This optimizer | Unique combination | **RESEARCH-PROTOTYPE** |

### 15. Three-level LRU query cache

| Feature | Paper/Work | Main Idea | Storage Model | Query Model | Math Foundation | Implementation | Benchmark | Limitations | Relationship to SheafDB | Potential Overlap | Novelty Assessment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Multi-level caching | CPU caches (L1/L2/L3) | Hierarchical cache | Cache lines | Locality | N/A | Hardware | Yes | Hardware-specific | Conceptual similarity | Low — different context | **KNOWN-COMMERCIAL** |
| | Database buffer pools | Pages in memory | Page cache | LRU/K-LRU | N/A | All DBMS | Yes | Page-level | SheafDB caches at query plan level | Low — different granularity | **KNOWN-COMMERCIAL** |
| 3-level query cache | SheafDB | parsed AST → logical plan → physical plan | LRU per level | Hit/miss | N/A | Python | Yes | Small scale | This implementation | — | **KNOWN** |

**Risk:** This is a simple OrderedDict-based LRU with three instances. There is nothing novel here. Every major database has substantially more sophisticated caching.

---

## Risks (features where novelty claims are weak)

1. **"Sheaf database system"** — The system is a Python prototype storing facts in dicts and SQLite. The sheaf condition (gluing) is checked at query time, not enforced at insert time. A reviewer may argue this is a presheaf database, not a sheaf database, since the sheaf condition is optional verification.

2. **"N-ary fact storage"** — RDF-star directly addresses n-ary facts. Property graphs store edge attributes. The claim that "KG requires decomposition into triples" is true for vanilla RDF, but not for modern extensions. A reviewer may ask: why not use RDF-star instead?

3. **"5 engine adapters"** — Three are stubs with `pass` implementations. The benchmark only compares two engines (KG and Sheaf). This should be honestly reported as "2 working adapters."

4. **"Cost-based optimizer"** — The cost model uses fixed heuristic values (`estimate_scan` returns 10.0 always, `estimate_join` returns `left_card * right_card * 0.1`). Cardinality estimates are not data-driven. This is a toy cost model.

5. **"Canonical model for cross-engine mapping"** — While the idea is strong, the CanonicalMapping class has only `to_canonical` and `from_canonical` methods with no schema validation, no type checking, no arity enforcement, and no error recovery. It's a thin wrapper.

6. **"Global section cache"** — Simple LRU with invalidation on every insert. No adaptive policies, no write-through, no persistence. A reviewer from the database community will find this trivial.

7. **"Sheaf query planner"** — The local/semi-local/global classification maps query types to open sets via if/else chains (40 lines of classification logic) with no cost model for which specific open sets to use. The "optimization" is limited to deduplication and a hard cap of 10 open sets.

8. **"Presheaf axioms verified"** — The identity restriction check and composition check only verify the system's own data structures are internally consistent, not that the mathematical axioms hold for non-trivial cases. The composition check compares set membership (fact IDs in open sets), not semantic equivalence of restricted facts.

---

## Summary Table

| Feature | Classification | Key Reason |
|---|---|---|
| Sheaf-theoretic data model | KNOWN | Textbook category theory |
| Finite topological space | KNOWN | Standard math (Alexandrov 1937) |
| Presheaf with restriction maps | KNOWN | Standard definition |
| Sheaf gluing | KNOWN | Trivial pairwise equality algorithm |
| Context poset | KNOWN | Prefix tree / trie data structure |
| Canonical model | **NOVEL** | Specific KG↔Sheaf mapping with injectivity |
| Cross-engine query equivalence | RESEARCH-PROTOTYPE | Novel verification framework |
| N-ary fact storage | KNOWN | RDF-star, property graphs, hypergraphs |
| Context-indexed sections | KNOWN | Named graphs / quad stores |
| Stalk-based query model | KNOWN-NOT-IMPLEMENTED | Standard math, no prior implementation |
| Global section cache | KNOWN | Standard LRU cache |
| Consistency checking | RESEARCH-PROTOTYPE | Automated sheaf axiom verification |
| Benchmark framework | KNOWN | Standard multi-engine benchmark |
| Cost-based optimizer | RESEARCH-PROTOTYPE | Novel cross-representation optimization |
| Three-level LRU cache | KNOWN | Standard multi-level cache |

**Bottom line:** 2 genuinely novel claims (canonical model mapping, cross-engine verification framework), 3 research-prototype claims (consistency checking, cost-based optimizer, query equivalence), 1 known-not-implemented (stalk model), and 9 known from prior work.
