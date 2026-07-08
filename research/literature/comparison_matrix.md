# SheafDB Comparison Matrix

Detailed comparison of SheafDB against major RDF stores, graph databases, and related formal systems.

---

## Feature Matrix

| Feature | Apache Jena | GraphDB | Blazegraph | Neo4j | Neptune | RDFox | Stardog | HyperGraphDB | FCA | SheafDB |
|---|---|---|---|---|---|---|---|---|---|---|
| **Storage Model** | RDF triple store (subject-predicate-object); TDB/TDB2 native storage | RDF triple store with native Sail storage; supports RDF* (reification as first-class) | RDF triple store; journal-based append-only; GPU-accelerated indexing | Property graph — labeled nodes and relationships with key-value properties | RDF triple store + property graph (SPARQL + Gremlin endpoints) | RDF triple store; parallel Datalog materialization; shared-nothing | RDF triple store with virtual graph / federation support | Directed hypergraph — edges can connect arbitrary sets of nodes | Formal context — binary incidence matrix (objects × attributes) | **Sheaf-theoretic fact store** — n-ary facts in context-indexed presheaves; no fixed schema; facts are sections over a poset of contexts |
| **Query Language** | SPARQL 1.1 (full), ARQ extension; OWL/RL via reasoner | SPARQL 1.1, RDF* queries, graph path expressions | SPARQL 1.1, BFS (GAS API) | Cypher (declarative property graph query lang); APOC procedures | SPARQL 1.1, Gremlin, openCypher (via Neptune DSQL) | SPARQL 1.1, Datalog rules (Prolog-like) | SPARQL 1.1, Datalog rules, graph path queries | Java API (embedded library, no standalone query language) | Concept lattice navigation (no general-purpose query lang) | **Not full SPARQL** — supports fact-pattern matching, context-walking, and sheaf restriction queries via a Python API; query expressiveness bounded by presheaf morphisms |
| **Mathematical Foundation** | Description logics (OWL 2 DL/RL/QL); relational algebra | RDF* / reification; description logics | RDF semantics; set-based triple indexing | Property graph model (labeled nodes, relationships, properties) | RDF (W3C semantics) + property graph (TinkerPop) | Datalog (stratified negation); parallel fixpoint semantics; RDF entailment | Description logics; Datalog; RDF entailment regimes | Directed hypergraph theory; algebraic topology | Order theory; lattice theory; Galois connections | **Sheaf theory** — facts are sections of a presheaf over a context poset; gluing axiom enforces local-global consistency; sheaf cohomology measures inconsistency |
| **Reasoning Support** | OWL, RDFS, rule-based (generic rule reasoner); pellet-like via external | OWL2 RL, RDFS, custom rulesets (embedded rule engine) | OWL2 RL (limited), RDFS (in-memory inference) | None (application-level; graph algorithms via GDS library) | OWL, RDFS (via Neptune inference engine) | OWL2 RL/RDF, built-in Datalog reasoner; parallel materialization | OWL2, RDFS, SWRL, Datalog rules (federated reasoning across sources) | None (no built-in reasoner) | Concept lattice / implication inference (attribute logic) | **Contextual reasoning** — consistency verified via sheaf gluing condition; no OWL or DL reasoning; can detect incompatible facts across contexts via sheaf condition |
| **Context Support** | Named graphs (quads); limited to graph-level context | RDF* named graphs; context managed via repository partitioning | Named graphs (quads) | None (no native context abstraction; labels approximate it) | Named graphs (quads), graph-level isolation | Namespaces / data sources; Datalog module system | Named graphs; virtual graphs for federation | None built-in (user-defined) | Formal contexts are the core structure (object × attribute × relation) | **Native context-indexed sheaves** — every fact lives in a context; contexts form a poset with restriction maps; no artificial N-triple graph boundary |
| **Temporal Support** | Named graphs + external versioning | RDF* reification for time; temporal indexes | None native (application-layer) | None native (APOC temporal, graph versioning plugins) | Time-to-live (TTL); point-in-time restore; no query-level temporal | Datalog rules over temporal data (user-defined) | Temporal reasoning via rule-based time modeling | None native | None native | **Context-as-time** — contexts can encode time intervals; restriction maps act as temporal projections; no dedicated temporal query language |
| **Provenance** | Named graphs for source tracking | RDF* reification for provenance metadata | None native | None native (audit logging only) | Audit logs; CloudTrail; no query-level provenance | Datalog provenance via rule derivation trees (why-not) | PROV-O support; graph-level provenance tracking | None native | Attribute implications (conceptual provenance) | **Sections track provenance** — each fact belongs to a specific context section; restriction maps preserve source identity; local-global proofs encode dependency chains |
| **Consistency Model** | ACID (TDB2); MVCC snapshots | ACID (RDF4J Sail); RDF* validation | Read-committed; eventual consistency on GPU paths | ACID (single instance); causal clustering (3.5+) | ACID within DC; eventual cross-region | Datalog fixpoint convergence (logical consistency) | ACID (single instance); read-committed cluster | ACID (embedded tx manager) | Lattice consistency (meet-join closure) | **Sheaf condition** — local facts must agree on overlaps; gluing axiom detects contradictions; sheaf cohomology quantifies inconsistency; single-node only |
| **Sheaf Theory** | None | None | None | None | None | None | None | Hypergraph graph model shares structural parallels (edges over arbitrary vertex sets) | Formal contexts form a category equivalent to a restricted class of sheaves on a two-element poset | **Core foundation** — entire data model is a presheaf; storage engine implements the sheaf category; gluing axiom is a runtime consistency check |
| **N-ary Facts** | Via reification (triple-as-resource) or RDF* | RDF* native n-ary relationships | Via reification | Via intermediate nodes (reification pattern) | Via reification or RDF* | Via Datalog rules over intermediate predicates | Via reification or RDF* | Hyperedge — native n-ary connections | Binary only (object–attribute) | **Native n-ary facts** — facts are functions from context to a tuple sort; arity is part of the sheaf signature; no reification overhead |
| **Cross-engine Equivalence** | None | None | None | None | None | None | Virtual graph federation across SPARQL endpoints | None | Concept lattice isomorphism theorems | **Sheaf morphisms as data transformations** — structure-preserving maps between sheaves provide a formal notion of query/view equivalence; proven equivalences via category theory |
| **Implementation** | Java (TDB/TDB2, Fuseki server) | Java (RDF4J-based, workbench) | Java (cluster, embedded) | Java (embedded, server, causal cluster) | Managed AWS service (proprietary) | C++ (Datalog engine, high perf) | Java (embedded, server, cloud) | Java (embedded library) | Various implementations (Concept Explorer, ToscanaJ) — Python/Java/R | **Python** (prototype); DuckDB-based storage layer; single-node; in-memory + optional DuckDB persistence |
| **Open Source** | Apache 2.0 | Proprietary (free tier available) | GPL 2.0 (older version BSD) | AGPL v3 (community) / commercial | Proprietary (AWS service) | Proprietary (free for research) | Proprietary (free tier available) | LGPL | Various (BSD/MIT depending on impl) | **MIT** |
| **Scalability to 10^6** | Yes — proven beyond 10^9 triples (TDB2) | Yes — billions of triples | Yes — billions (GPU sharded) | Yes — billions of nodes/edges | Yes — managed AWS at exabyte scale | Yes — optimized for 10^9+ with parallelism | Yes — billions of triples | Unknown (small-scale applications) | N/A (typically small formal contexts) | **~10^5 limit** — in-memory sheaf construction; DuckDB persistence not optimized for sheaf operations; known scalability bottleneck |

---

## Key Differentiators

1. **Sheaf-theoretic semantics** — SheafDB is the only database whose data model, query semantics, and consistency verification are grounded in sheaf theory and the gluing axiom. No other system uses presheaves, restriction maps, or sheaf cohomology as native concepts.

2. **Local-global consistency** — The sheaf condition provides a mathematically rigorous definition of "consistent data": facts assigned to overlapping contexts must agree on the intersection. This yields automatic contradiction detection without constraint rule writing.

3. **Native n-ary facts** — Unlike RDF triples (always binary) and property graphs (binary edges), SheafDB treats n-ary facts as first-class citizens. A fact can relate any number of entities without reification overhead.

4. **Context-indexed namespaces** — Contexts form a partially ordered set, not a flat set of named graphs. Restriction maps (fact projection) are a formal operation, enabling precise queries over granular sub-contexts.

5. **Sheaf morphisms as query equivalences** — Structure-preserving maps between sheaves provide a category-theoretic notion of query equivalence, view transformation, and data integration — unmatched in relational or graph systems.

---

## Overlapping Features

| Feature | Also found in | SheafDB's treatment |
|---------|---------------|---------------------|
| Named graphs / contexts | Jena, GraphDB, Blazegraph, Neptune, Stardog | Contexts form a poset with restriction maps, not just a flat set |
| N-ary relationships | HyperGraphDB, RDF* (GraphDB, Stardog) | Native in the sheaf signature — no reification pattern needed |
| Consistency checking | RDFox (Datalog stratification), GraphDB (SHACL) | Mathematically grounded in the gluing axiom; automatic, not rule-based |
| Open source | Jena (Apache 2.0), Blazegraph (GPL/BSD), Neo4j (AGPL) | MIT license |
| SPARQL subset | All RDF stores | SheafDB does not implement full SPARQL 1.1; only pattern-matching subset |
| Datalog-like entailment | RDFox, Stardog | Not yet implemented; no rule engine as of 2024 |
| Formal / lattice structure | FCA (Ganter & Wille) | FCA is a special case of the sheaf model over a two-element poset |
