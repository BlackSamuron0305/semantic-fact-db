# SheafDB — Risk Register

> Risks to paper acceptance and project validity, with mitigation strategies and current status.

---

### R1: Novelty is weak

- **Risk**: SheafDB applies known mathematics (sheaf theory) to a different domain. The individual components (topology, presheaf, gluing) are all standard category theory. Reviewers may see this as a "trivial rebranding" rather than a genuine contribution.
- **Probability**: HIGH
- **Impact**: HIGH
- **Mitigation**: Clearly articulate the novel *combination* and the engineering insights required to make sheaf semantics tractable for databases. Emphasize that prior work used sheaves for *querying* existing databases (Patterson 2022), not as a *storage model*. Highlight specific design decisions (context poset, restriction maps, gluing algorithm) that are non-trivial and not found in category theory textbooks.
- **Evidence required**: Explicit comparison in the paper's "Related Work" section showing what SheafDB adds beyond textbook category theory. A clear statement of the *technical* contribution (e.g., "first system to use presheaves as a physical data layout").
- **Current status**: Not addressed.

---

### R2: Patterson 2022 pre-empts novelty

- **Risk**: If Patterson already proposed sheaf-theoretic databases, then SheafDB is "just an implementation." The core conceptual novelty would be attributed to prior art.
- **Probability**: MEDIUM
- **Impact**: HIGH
- **Mitigation**: Cite Patterson 2022 precisely and distinguish SheafDB's contribution. Determine whether Patterson proposed sheaves as a *specification language* (schema-level) vs. SheafDB's use as a *runtime representation* (instance-level). If Patterson's work is theoretical, SheafDB's engineering/implementation contribution stands.
- **Evidence required**: A detailed "Differences from Patterson (2022)" subsection. Ideally a direct comparison table showing what Patterson described vs. what SheafDB implements.
- **Current status**: Not addressed.

---

### R3: Performance is worse than baselines

- **Risk**: SheafDB latency is ~2× KG for all query types (2.4 µs vs 4.4 µs average). If there is no query regime where SheafDB wins, the entire contribution is questionable.
- **Probability**: HIGH
- **Impact**: HIGH
- **Mitigation**: Identify and benchmark a specific workload where SheafDB's structure offers an advantage (e.g., queries that benefit from context locality, multi-context queries, or queries where KG's index overhead dominates). Benchmark at larger scales where KG's O(N) characteristics may hurt. Alternatively, argue that SheafDB's advantage is not raw speed but *correctness guarantees* (e.g., gluing consistency), making the speed comparison secondary.
- **Evidence required**: A benchmark showing at least one class of query or dataset scale where SheafDB matches or beats KG.
- **Current status**: Not addressed.

---

### R4: Benchmark bias

- **Risk**: Benchmark uses only synthetic data, small scales (100–10K facts), and limited query types (15). Real-world performance may differ significantly.
- **Probability**: MEDIUM
- **Impact**: MEDIUM
- **Mitigation**: Add larger synthetic scales (100K–1M facts). If timings permit, run against a real-world subset (e.g., a slice of Wikidata). Include query types that stress SheafDB's strengths (multi-context queries, update-heavy workloads).
- **Evidence required**: Results at 100K+ fact scale and/or a real-world dataset.
- **Current status**: Not addressed.

---

### R5: Scalability wall

- **Risk**: O(|C|·N²) worst-case for gluing means the system does not scale beyond ~10⁵ facts. This would make SheafDB impractical for any real-world knowledge graph.
- **Probability**: MEDIUM
- **Impact**: HIGH
- **Mitigation**: Provide empirical scaling curves showing runtime vs. N for gluing queries. Profile to identify the bottleneck and consider optimizations (e.g., indexing restriction maps, caching gluings for repeated queries, approximating gluing with sampling). If scalability is fundamentally limited, explicitly characterize the feasible regime (e.g., "SheafDB targets medium-scale curated graphs < 10⁵ facts, not web-scale KBs").
- **Evidence required**: Scaling plots up to at least 10⁵ facts showing gluing time. Ideally a theoretical bound proof and empirical validation.
- **Current status**: Not addressed.

---

### R6: Restriction map explosion

- **Risk**: Storing restriction maps for all pairs of comparable contexts adds O(|C|²) overhead, which dominates memory for any non-trivial context poset.
- **Probability**: HIGH
- **Impact**: MEDIUM
- **Mitigation**: Measure the actual number of restriction maps stored vs. |C|² upper bound for typical context posets (prefix-based). If the poset is a tree, |C|² becomes O(|C|·depth). Propose lazy generation or on-the-fly computation for infrequently accessed maps.
- **Evidence required**: Empirical measurement of restriction map count and memory for growing |C|. Demonstration that effective overhead is sub-quadratic for realistic posets.
- **Current status**: Not addressed.

---

### R7: Memory growth from per-fact storage in multiple open sets

- **Risk**: Each fact is stored in multiple open sets, amplifying memory usage by a factor proportional to the average number of contexts a fact participates in.
- **Probability**: MEDIUM
- **Impact**: MEDIUM
- **Mitigation**: Measure the amplification factor empirically across different context configurations. Compare total memory vs. KG baseline. Consider deduplication or pointer-based sharing of fact payloads.
- **Evidence required**: Memory usage comparison at multiple scales showing the amplification factor. Discussion of the trade-off (memory cost vs. query simplicity).
- **Current status**: Not addressed.

---

### R8: Stub engine adapters

- **Risk**: 3 of 5 engine adapters (Jena, Blazegraph, Neo4j) may be stubs or not fully functional, weakening the "fair comparison" claim in the evaluation.
- **Probability**: HIGH
- **Impact**: HIGH
- **Mitigation**: Audit each adapter. Either complete them to functional parity with KG/SheafDB backends, or explicitly state which adapters are stubs and exclude them from benchmarks. Do not claim "comparison against 5 engines" if only 2 are real.
- **Evidence required**: A test suite that exercises each adapter with the full benchmark query set. Documentation of which adapters are production-ready vs. experimental.
- **Current status**: Not addressed.

---

### R9: Context poset limited to prefix-based ordering

- **Risk**: Real-world contexts may not fit a prefix-based hierarchical model. Overlapping, non-hierarchical, or cyclic context structures cannot be represented.
- **Probability**: MEDIUM
- **Impact**: MEDIUM
- **Mitigation**: Acknowledge the limitation explicitly. Characterize the class of real-world knowledge organization systems that *do* fit prefix ordering (e.g., file systems, URL hierarchies, ontology subsumption). Discuss how the model could be extended to arbitrary posets (at additional cost).
- **Evidence required**: A "Limitations" section in the paper describing the expressiveness boundary. Optionally, a case study mapping a real-world hierarchy onto the prefix model.
- **Current status**: Not addressed.

---

### R10: Theorem proofs may have gaps

- **Risk**: The paper claims 8 theorems. Not all may be formally verified and could contain edge-case errors that a reviewer would spot.
- **Probability**: LOW
- **Impact**: HIGH
- **Mitigation**: Formalize key theorems in a proof assistant (e.g., Coq, Agda, Lean) or at minimum write detailed proof sketches with all preconditions and edge cases checked. Have a colleague who is not an author review the proofs.
- **Evidence required**: Supplementary material with full proofs. Ideally a mechanized proof for the central gluing theorem.
- **Current status**: Not addressed.

---

### R11: Evaluation not on standard benchmarks

- **Risk**: Not using LUBM, SP2Bench, BSBM, or other established RDF benchmarks limits comparability with prior work and makes it difficult for reviewers to assess performance claims.
- **Probability**: HIGH
- **Impact**: MEDIUM
- **Mitigation**: Adapt at least one standard benchmark (LUBM is simplest) to SheafDB's data model. If the custom schema/context model prevents direct mapping, explicitly state why standard benchmarks are inapplicable and propose a community benchmark for context-based databases.
- **Evidence required**: Benchmark results on a recognized standard, or a well-reasoned argument for why existing benchmarks are unsuitable, plus a proposed alternative.
- **Current status**: Not addressed.

---

### R12: Missing competitor comparison

- **Risk**: No actual comparison against Jena, Neo4j, or GraphDB appears in benchmark results (adapters may be stubs). The evaluation compares SheafDB only against KG, which is insufficient to claim "comprehensive evaluation."
- **Probability**: MEDIUM
- **Impact**: HIGH
- **Mitigation**: Ensure at least one well-known RDF store (e.g., Apache Jena) is fully integrated and benchmarked. If integration is impossible, include published performance numbers from the literature as an approximate baseline (with caveats).
- **Evidence required**: Benchmark table with at least one external system (Jena, Neo4j, or similar) alongside SheafDB and KG.
- **Current status**: Not addressed.

---

### R13: Single-node limitation

- **Risk**: Real-world knowledge graphs are deployed on distributed systems (Neptune, RDFox, JanusGraph). A single-node comparison is not representative of production environments.
- **Probability**: LOW
- **Impact**: MEDIUM
- **Mitigation**: Explicitly scope the claims to single-node deployments. Discuss the theoretical challenges of distributing sheaf-based storage (e.g., gluing across nodes, distributed restriction maps). If possible, sketch a distributed architecture without requiring a full implementation.
- **Evidence required**: A section on "Distributed SheafDB" discussing feasibility, expected bottlenecks, and how the model maps to distributed systems. Acknowledge as future work.
- **Current status**: Not addressed.

---

### R14: Query language is custom

- **Risk**: SheafDB's query language is not SPARQL 1.1 compliant, limiting applicability and making it impossible for reviewers to compare expressiveness directly with standard RDF systems.
- **Probability**: HIGH
- **Impact**: MEDIUM
- **Mitigation**: Provide a mapping from SheafDB queries to SPARQL (or a subset thereof). If full SPARQL is not supported, clearly characterize the fragment that is. Discuss which SPARQL features are impossible/infeasible under the sheaf model.
- **Evidence required**: A "SPARQL compatibility" table showing which SPARQL 1.1 features are supported, partially supported, or unsupported. Example translations.
- **Current status**: Not addressed.

---

### R15: No real-world use case

- **Risk**: No evaluation on any real-world dataset (Wikidata, DBpedia, etc.). This makes it hard to argue that SheafDB solves a real problem.
- **Probability**: HIGH
- **Impact**: MEDIUM
- **Mitigation**: Identify a real-world dataset or scenario where context-sensitive querying is valuable (e.g., versioned knowledge graphs, multi-provenance integration, biomedical ontologies with context-dependent facts). Run a case study showing how SheafDB's gluing semantics catches inconsistencies that other systems miss.
- **Evidence required**: A case study (even small-scale) using a real or realistic dataset with qualitative and quantitative results.
- **Current status**: Not addressed.

---

### R16: System maturity and reproducibility

- **Risk**: As a research prototype, the codebase may have undocumented dependencies, missing configuration, or environment-specific behavior that prevents reviewers from reproducing results.
- **Probability**: MEDIUM
- **Impact**: LOW
- **Mitigation**: Provide a Docker image and/or a reproducible environment script (`Dockerfile`, `nix`, or `conda-lock`). Include a "Reproducing results" section in the README with exact commands, expected runtimes, and output checksums.
- **Evidence required**: A reviewer (or third party) can clone the repo, run one command, and reproduce the benchmark tables from the paper.
- **Current status**: Not addressed.

---

### R17: Community and adoption risk

- **Risk**: Even if the paper is accepted, the project may see no adoption due to the dominance of RDF, Property Graphs, and vector databases. A novel storage model requires significant ecosystem investment (tooling, query languages, integrations).
- **Probability**: HIGH
- **Impact**: LOW (on paper acceptance; HIGH on project longevity)
- **Mitigation**: Release as open-source with permissive license. Invest in SPARQL compatibility and export/import tooling. Publish a clear migration guide for users of existing RDF stores. Target a niche (e.g., provenance tracking, biomedical context-dependent facts) where the sheaf model offers clear advantages.
- **Evidence required**: External contributors, a published use case from an early adopter, or integration with an existing data pipeline.
- **Current status**: Not addressed.
