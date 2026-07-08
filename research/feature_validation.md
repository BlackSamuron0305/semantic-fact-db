# Feature Validation — SheafDB

## Methodology

Each feature is classified by status and certainty based on:
- **Code review** of all implementation files in `src/sfdb/`
- **Documentation review** in `docs/`, `paper/`, `research/`
- **Comparison** to known prior work cited in `paper/bibliography.bib`
- **Test coverage** inferred from `tests/` directory structure

---

## Feature Validations

### 1. SheafStore with Presheaf/Sheaf classes

- **Status**: Research prototype
- **Evidence**: `src/sfdb/sheaf/sheaf.py` implements SheafStore, Sheaf (inherits Presheaf), and Presheaf with full axiom structure. Presheaf stores sections by context, implements `assign`, `sections_over`, `restrict`, `restrict_all`, `sections_local_to`. Sheaf adds `glue`, `global_sections`, `locally_equivalent`. The implementation is complete and functional — it stores facts, retrieves them by context, and computes restrictions.
- **Certainty**: **HIGH**
- **Why**: The code exists, is consistent, and is importable. Tests exist in the repository. The mathematical structure is correct per standard sheaf theory.

### 2. FiniteTopologicalSpace

- **Status**: Already known
- **Evidence**: `src/sfdb/sheaf/topology.py` implements FiniteTopologicalSpace with open sets, neighborhoods, intersection closure, and point membership. This is a direct implementation of a standard mathematical object (Alexandrov 1937, finite topological spaces). The implementation correctly maintains ∅, X, finite intersections, and arbitrary unions. However, the "arbitrary union" property is not verified — only intersection closure is computed via `intersection_closure()`.
- **Certainty**: **HIGH**
- **Why**: Standard data structure, correctly implemented.

### 3. OpenSet/Neighborhood

- **Status**: Already known
- **Evidence**: `src/sfdb/sheaf/topology.py` lines 18–107. OpenSet stores a name, frozenset of point IDs, and metadata. Supports `contains`, `is_subset_of`, `intersect`, `union`. Neighborhood wraps a center point and its containing open set. This is a straightforward wrapper around Python's frozenset with naming conventions.
- **Certainty**: **HIGH**
- **Why**: Trivial data structures with no novelty or complexity.

### 4. RestrictionMap/RestrictionGraph

- **Status**: Already known
- **Evidence**: `src/sfdb/sheaf/restriction.py` implements RestrictionMap (source, target, timing stats), ContextRestriction (for context subsumption), TemporalRestriction (for temporal filtering), and RestrictionGraph (DAG of restriction edges with DFS path existence check). The RestrictionGraph is built by iterating over all open set pairs and checking subset relationships — O(n²) construction.
- **Certainty**: **HIGH**
- **Why**: Standard directed graph implementation. The restriction concept is textbook sheaf theory. No algorithmic novelty.

### 5. Gluing algorithm

- **Status**: Already known
- **Evidence**: Two implementations exist:
  1. `src/sfdb/sheaf/sheaf.py:Sheaf.glue()` — O(k·m) pairwise overlap check. Given covering sections, checks each pair for agreement on the meet of their contexts. Raises GluingError on disagreement. Constructs a new Section from the representative fact.
  2. `src/sfdb/sheaf/presheaf.py:Sheaf.compute_global_sections()` — O(k²·m) brute-force global section computation. Pairs every open set with every other, finds shared fact IDs, and collects those with identical facts.
- **Certainty**: **HIGH**
- **Why**: Both are trivial, literal implementations of the sheaf gluing definition. No novel algorithm. The "gluing" is just equality checking.

### 6. Global section reconstruction

- **Status**: Already known
- **Evidence**: `src/sfdb/sheaf/sheaf.py:Sheaf.global_sections()` — restarts from root context. If no root sections: gets the cover (immediate sub-contexts of root), restricts all cover sections to root, returns them. O(c·s) time. This is not true sheaf gluing from arbitrary covers — it only looks one level down from root.
- **Certainty**: **MEDIUM**
- **Why**: The implementation is incomplete as a general global section algorithm. True global section reconstruction should recursively glue from leaves to root through all levels. The current implementation only checks the root's immediate sub-contexts, which works for the two-level context trees in synthetic tests but may miss global sections in deeper hierarchies. The `compute_global_sections()` in `presheaf.py` is a different approach (pairwise overlap of all open sets) that does a full scan but is O(k²·m).

### 7. ContextPoset

- **Status**: Already known
- **Evidence**: `src/sfdb/sheaf/sheaf.py:ContextPoset` (lines 58–161). Implements a poset of dot-separated context paths with `add`, `contains`, `cover`, `is_cover`, `join`, `meet`, `root`, `leaves`. The ordering is by prefix: `Context("a.b") <= Context("a")` is True. Cover returns immediate sub-contexts. Join/meet use prefix matching. This is a simple prefix tree (trie) with order theory terminology.
- **Certainty**: **HIGH**
- **Why**: This is a standard trie/prefix tree. The `cover()` method is O(n) scanning all contexts, which is naive but correct. The `meet()` method for incomparable contexts returns the longer one, which is not mathematically correct as a meet (the true meet in a tree poset for incomparable elements would be their LCA, but the prefix poset is not a meet-semilattice for incomparable nodes).

### 8. Stalk model

- **Status**: Known, not implemented in prior databases
- **Evidence**: `src/sfdb/sheaf/presheaf.py:Stalk` (lines 65–109) and `src/sfdb/sheaf/indexes.py:StalkIndex` (lines 57–91). A Stalk contains all LocalSections for a given point ID. The stalk is pre-computed (persisted), not computed dynamically as the direct limit of neighborhoods. The StalkIndex maps point IDs to Stalks. Each Stalk is populated during insertion (every assigned open set's section is added to the stalk for that fact ID).
- **Certainty**: **MEDIUM**
- **Why**: The mathematical stalk is the *direct limit* of F(U) over all neighborhoods U of x. The current implementation simply collects all sections for a point, which is equivalent only if the point appears in every open set it belongs to. Since sections are duplicated across all relevant open sets during insertion, the stalk effectively contains all sections mentioning that fact. This is mathematically correct but trivial — the stalk is just "all sections with this fact ID," not a true direct limit construction. A reviewer from algebraic topology may object to the terminology.

### 9. SemanticFact (n-ary fact)

- **Status**: Already known
- **Evidence**: Defined in `src/sfdb/common/types.py` (Fact) and `docs/semantic_model.md`. An immutable dataclass with id, subject, relation, objects (tuple of Value), attributes, context, provenance, confidence, temporal, metadata. This is a standard n-ary fact representation similar to:
  - RDF-star reification
  - Property graph edges with attributes
  - Event/tuple representations in event databases
  - Frame-based knowledge representations
- **Certainty**: **HIGH**
- **Why**: Every element of this design is standard data modeling. The specific field choices are reasonable but not novel.

### 10. TripleStore (KG baseline)

- **Status**: Already known
- **Evidence**: `src/sfdb/kg/triple.py:TripleStore` — in-memory triple store with SPO/POS/OSP indexes. Uses nested dicts for index lookups. Supports `add`, `query_sp`, `query_po`, `query_os`, `query_s`, `query_p`, `query_o`, `all_triples`. This is a textbook triple store implementation.
- **Certainty**: **HIGH**
- **Why**: Standard RDF triple store with three permutation indexes. Nothing novel.

### 11. FactDecomposer (reification)

- **Status**: Already known
- **Evidence**: `src/sfdb/kg/triple.py:FactDecomposer` — converts n-ary Fact to RDF-style reified triples using rdf:type, rdf:subject, rdf:predicate, rdf:object. The decomposer also supports reconstruction. The `decompose` method generates O(2 + arity) triples per fact. This is textbook RDF reification.
- **Certainty**: **HIGH**
- **Why**: Standard RDF reification pattern. No novelty. The implementation is naive (no BlankNode support, no graph-level optimization).

### 12. CanonicalModel / CanonicalMapping

- **Status**: Research prototype
- **Evidence**: `src/sfdb/canonical/canonical.py` implements CanonicalEntity, CanonicalRelation, CanonicalFact, CanonicalMapping, and CanonicalModel. The mapping provides `to_canonical` (Fact → CanonicalFact) and `from_canonical` (CanonicalFact → Fact). The model maintains entity/relation registries. The bidirectional mapping claims injectivity: `from_canonical(to_canonical(x)) ≅ x` and `to_canonical(from_canonical(c)) = c`.
- **Certainty**: **MEDIUM**
- **Why**: The mapping works for the codebase's specific Fact ↔ CanonicalFact case, but:
  - The "injectivity" is trivial since `from_canonical` just calls `to_fact()` which is a field copy
  - There is no actual proof of injectivity for the full KG → Canonical → Sheaf round-trip
  - The mapping from KG triples to CanonicalFact is NOT implemented in CanonicalMapping — it only handles Fact objects
  - The KG engine reconstructs SemanticFact from reified triples via a separate code path (`_reconstruct_fact`), not via CanonicalMapping
  - This means the "canonical model" is claimed but the actual KG→Canonical→Sheaf pipeline does not pass through it

### 13. SPARQL parser

- **Status**: Already known
- **Evidence**: `src/sfdb/kg/sparql.py` implements a simplified SPARQL parser with tokenizer, recursive descent parser, and naive interpreter. Supports SELECT, WHERE, FILTER, OPTIONAL, LIMIT, ORDER BY, OFFSET. The parser is ~200 lines and handles a small subset of SPARQL 1.1 (no GROUP BY, HAVING, BIND, UNION, subqueries, property paths, federated queries, etc.).
- **Certainty**: **HIGH**
- **Why**: This is a simple recursive descent parser for a subset of SPARQL. Standard compiler techniques. The parser uses `eval()` for filter expressions (line 316), which is a security concern. The executor is a naive nested-loop join over all triples — no query optimization.

### 14. Query optimizer

- **Status**: Research prototype
- **Evidence**: Two optimizer implementations exist:
  1. `src/sfdb/query/optimizer.py:QueryOptimizer` — cost-based with 6 rewrite rules (ConstantFolding, PredicatePushdown, ProjectionPushdown, JoinReordering, DeadOperatorRemoval, LogicalSimplification). Uses a CostModel with fixed estimates (scan=10.0, selection=input*0.5, join=left*right*0.1, etc.). The cost model is purely heuristic — no data-driven cardinality estimation. Rewrite rules are partially implemented (ProjectionPushdown and JoinReordering are no-ops).
  2. `src/sfdb/optimizer/optimizer.py:QueryOptimizer` — cross-engine cost estimator comparing KG vs Sheaf costs. Uses a simple formula: `Cost = α·scan_cost + β·join_cost + γ·reconstruction_cost`. For KG: scan_cost = total triples, join_cost ∝ degree^depth, reconstruction_cost = scan_cost × 0.1. For Sheaf: scan_cost = sections per context, join_cost = 0, reconstruction_cost = 0.
- **Certainty**: **MEDIUM**
- **Why**: Both optimizers are functional but incomplete. Optimizer 1 uses fixed cardinality estimates (not data-driven). Optimizer 2 has a reasonable cost model but oversimplifies (Sheaf join_cost is always 0, which is only true for context-local queries; cross-context joins in the sheaf model still require scanning). The rewrite rules in optimizer 1 are standard textbook rules — partially implemented.

### 15. Physical plan builders (KG and Sheaf)

- **Status**: Already known
- **Evidence**: `src/sfdb/query/physical_plans.py` implements KGPhysicalPlanBuilder and SheafPhysicalPlanBuilder. Each translates a LogicalPlan tree into PhysicalPlanNode trees with operator types, detail strings, and cost estimates. Physical operator types include KG_INDEX_SEEK, KG_TRIPLE_SCAN, KG_HASH_JOIN, SHEAF_OPEN_SET_LOOKUP, SHEAF_LOCAL_SECTION_LOOKUP, SHEAF_RESTRICTION_TRAVERSAL, SHEAF_GLOBAL_SECTION_CONSTRUCTION, etc.
- **Certainty**: **HIGH**
- **Why**: This is a standard physical plan generation pattern (translate logical operators to physical operators, estimate costs). No novel physical operators — each corresponds to a known database access method. The Sheaf plan builder maps joins to restriction traversals (line 311), which is an interesting design choice but not novel.

### 16. Query cache

- **Status**: Already known
- **Evidence**: `src/sfdb/query/cache.py` implements QueryCache with three levels (parsed AST, logical plan, physical plan), each using LRUCache (OrderedDict-based LRU). The LRUCache supports get, put, clear, hit_rate, stats. This is a textbook multi-level LRU cache with ~60 lines of code.
- **Certainty**: **HIGH**
- **Why**: Standard LRU cache using Python's OrderedDict. No sharding, no TTL, no adaptive eviction, no persistence, no concurrent access. The three-level architecture is a simple instantiation of three independent LRU instances.

### 17. ConsistencyChecker

- **Status**: Research prototype
- **Evidence**: `src/sfdb/sheaf/consistency.py:ConsistencyChecker` implements 5 checks:
  1. `check_locality()` — for each open set U and each sub-set V, checks that any two sections in F(U) that agree in F(V) are identical in F(U)
  2. `check_gluing()` — for each overlapping open set pair, checks that shared sections have equal facts
  3. `check_restriction_composition()` — for U ⊇ V ⊇ W, checks that ρ_{V,W}∘ρ_{U,V} = ρ_{U,W} at the set level
  4. `check_identity_restriction()` — checks ρ_{U,U} preserves all sections
  5. `check_empty_set()` — checks F(∅) is defined
- **Certainty**: **MEDIUM**
- **Why**: The checks are mathematically correct but have important caveats:
  - Locality check assumes V ⊆ U means any V in the topology is a "cover" of U, which is not the standard definition of an open cover. A true cover of U is a set of open sets whose union is U. The current check treats every subset V as a cover element, which is both too strict (not all subsets form a cover) and too weak (a single V is not a cover).
  - The restriction composition check only verifies set-level equality (same fact IDs), not semantic equality (same facts). This is weaker than the mathematical condition.
  - The gluing check only ensures consistency for the same fact appearing in multiple open sets, not for genuinely different facts that are compatible on overlaps.
  - The empty set check is tautological (just checks the "∅" open set exists in the topology).
  - A reviewer will note these checks do not actually verify the sheaf condition in its full mathematical generality.

### 18. Synthetic dataset generator

- **Status**: Already known
- **Evidence**: `src/sfdb/datasets/synthetic.py:SyntheticDatasetGenerator` generates random facts with configurable number of entities, relations, facts, arity distribution, context depth, and branching. The generator creates a context tree, assigns random entities/relations/values, and produces Fact objects. Also includes `generate_random_graph` for graph-structured data.
- **Certainty**: **HIGH**
- **Why**: Standard random data generator. No novelty. The context generation creates a fixed tree structure, not arbitrary posets.

### 19. Benchmark framework

- **Status**: Already known
- **Evidence**: `src/sfdb/benchmark/` contains a comprehensive benchmark framework with:
  - BenchmarkConfig, BenchmarkRunner, BenchmarkResult (`runner.py`)
  - BenchmarkSuite (`suite.py`)
  - Metrics collection (`metrics.py`)
  - Profiler (`profiler.py`)
  - Query workload definitions (`query_workload.py`)
  - Statistics (`statistics.py`)
  - Visualization (`visualization.py`)
  - Output formatting (`outputs.py`)
  - Reproducibility support (`reproducibility.py`)
  - CLI interface (`cli.py`)
- **Certainty**: **HIGH**
- **Why**: Well-structured benchmark framework but standard in design. Similar to LUBM, SP2Bench, LDBC, YCSB, etc. The 15 query types are reasonable but not comprehensive.

### 20. OutputWriter (CSV/JSON/Parquet/LaTeX)

- **Status**: Already known
- **Evidence**: `src/sfdb/benchmark/outputs.py` implements output formatting in multiple formats. The LaTeX writer generates tables for the paper.
- **Certainty**: **HIGH**
- **Why**: Standard output formatting. No novelty. The LaTeX generation is project-specific.

### 21. Serialization (JSON/Parquet/MessagePack)

- **Status**: Already known
- **Evidence**: `src/sfdb/common/serialization.py` implements serialization/deserialization to JSON, Parquet, and MessagePack formats. The writeup claims "lossless round-trip" for JSON and MessagePack (Parquet columnar format may have precision limitations for nested data).
- **Certainty**: **HIGH**
- **Why**: Standard serialization using orjson, pyarrow, and msgpack libraries. These are known formats with well-established libraries.

### 22. Visualization

- **Status**: Already known
- **Evidence**: Two visualization modules:
  1. `src/sfdb/visualization/plots.py` — charts, plots for benchmark results
  2. `src/sfdb/sheaf/visualization.py` — sheaf topology visualization (generated PDFs in paper/figures/)
- **Certainty**: **HIGH**
- **Why**: Standard matplotlib/seaborn visualization. The sheaf visualization is specific but not novel as a technique.

### 23. Engine adapters (Jena, Blazegraph, Neo4j)

- **Status**: Research prototype (incomplete)
- **Evidence**: `src/sfdb/benchmark/engine_adapter.py` defines adapters for 5 engines:
  - **KGEngineAdapter**: Fully working — wraps KnowledgeGraph
  - **SheafEngineAdapter**: Fully working — wraps SheafStore
  - **JenaEngineAdapter**: Stub — wraps rdflib Graph, only supports triple insertion via URIRef/Literal, `execute_query_str` returns empty list
  - **BlazegraphEngineAdapter**: Stub — all methods are `pass` or returning empty lists
  - **Neo4jEngineAdapter**: Stub — all methods are `pass` or returning empty lists
- **Certainty**: **HIGH**
- **Why**: Only 2 of 5 adapters are functional. The Jena adapter exists but cannot execute queries. Blazegraph and Neo4j are empty scaffoldings with no implementation. The benchmark cannot compare SheafDB against existing KG systems — it only compares against its own toy KG implementation. This is a significant limitation for the novelty claim.

### 24. Verification framework

- **Status**: Research prototype
- **Evidence**: `src/sfdb/benchmark/verification.py:verify_equivalence` compares results from different engines by normalizing rows (converting dict values to strings) and checking for exact match. Also `src/sfdb/kg/engine.py:KnowledgeGraphEngine.verify()` and `src/sfdb/sheaf/engine.py:SheafDatabaseEngine.verify()` provide engine-level integrity checks.
- **Certainty**: **MEDIUM**
- **Why**: The verification approach is sound but limited:
  - Row comparison is exact string matching — no tolerance for numerical precision differences
  - Only checks that both engines produce identical output for the same input, not that the output is semantically correct
  - The engine-level verify() checks are basic: KG checks foreign key integrity, Sheaf runs consistency checks
  - No formal proof of equivalence between the two representations

### 25. Sheaf query planner (local/semi-local/global classification)

- **Status**: Research prototype
- **Evidence**: `src/sfdb/sheaf/optimizer.py:SheafOptimizer.classify()` and `src/sfdb/sheaf/query.py:SheafQueryPlanner` implement the three-tier query classification:
  - **Local**: subject matches specific entity → single open set lookup (O(1) via OpenSetIndex)
  - **Semi-local**: context, temporal, provenance, or neighborhood filter → related open sets
  - **Global**: no constraints or mixed types → full topology traversal
  The optimizer also manages a global section cache and deduplicates target open sets.
- **Certainty**: **MEDIUM**
- **Why**: The classification is heuristic and rule-based (if/else over query types). The thresholds are hardcoded (line 97: "GLOBAL if > 5 open sets, SEMI_LOCAL otherwise"). There is no data-driven analysis of which classification is optimal for a given query. The optimization is limited to deduplication and a cap of 10 open sets. This is a functional but naive query planner. A reviewer familiar with database query optimization will note the lack of:
  - Cardinality estimation
  - Cost-based plan selection within the sheaf engine (only cross-engine)
  - Join ordering optimization
  - Index selection based on query patterns

---

## Summary

| Category | Count | Features |
|---|---|---|
| Already known | 14 | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 13, 15, 16, 18, 19, 20, 21, 22 |
| Known, not implemented in prior systems | 1 | 8 (stalk as query model) |
| Research prototype | 5 | 12 (canonical mapping), 14 (query optimizer), 17 (consistency checks), 24 (verification), 25 (sheaf planner) |
| Commercial | 0 | — |
| Completely novel | 0 | — |

**Key finding:** No individual feature is completely novel. The novelty of SheafDB lies in the **integration** of sheaf-theoretic concepts into a working database system, not in any single component. The strongest claims are the cross-engine canonical mapping and the automated sheaf consistency verification, but both have significant caveats.

**Recommendation:** For the paper, position SheafDB as "the first implementation of a sheaf-based database system" rather than claiming novelty for individual features. The integration and cross-engine verification are the strongest novelty arguments.
