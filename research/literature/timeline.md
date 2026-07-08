# SheafDB: Research Timeline

Chronological overview of key developments leading to SheafDB.

---

| Year | Event | Significance to SheafDB | Relevance |
|------|-------|------------------------|-----------|
| 1960s–70s | Category theory foundations; sheaf theory developed in algebraic geometry (Grothendieck, et al.) | Provides the mathematical bedrock for sheaf-theoretic data modeling — local-global consistency, gluing conditions, presheaf structure | HIGH |
| 1992 | Mac Lane & Moerdijk, *Sheaves in Geometry and Logic* | Standard reference for sheaf theory via toposes; formalizes sheaves as presheaves satisfying a gluing axiom, which directly inspires SheafDB's consistency model | HIGH |
| 1995 | Abiteboul, Hull, Vianu, *Foundations of Databases* | Canonical text on database theory (relational, object-oriented, deductive); defines formal yardsticks SheafDB measures against | MEDIUM |
| 1999 | Ganter & Wille, *Formal Concept Analysis* | Introduces FCA — lattice-theoretic structure isomorphic to a restricted class of sheaves; conceptual link between order theory and context-aware data | MEDIUM |
| 2001 | Berners-Lee, Hendler, Lassila, "The Semantic Web" (Scientific American) | Lays out the Semantic Web vision that motivates RDF, OWL, and linked-data architectures that SheafDB extends with sheaf-theoretic context | MEDIUM |
| 2004 | RDF — W3C Recommendation | Core data model for Semantic Web; SheafDB's fact model generalizes RDF triples to n-ary facts (subject-predicate-object → context-indexed families) | HIGH |
| 2005 | LUBM (Lehigh University Benchmark) | Standard benchmark for OWL/RDF reasoning systems; establishes evaluation methodology that SheafDB may eventually adopt for comparison | LOW |
| 2008 | Angles & Gutierrez, "Survey of Graph Database Models" | Comprehensive taxonomy of graph data models; clarifies where property graphs differ from RDF — SheafDB's hybrid approach draws from both | MEDIUM |
| 2009 | Carlsson, "Topology and Data" (TDA paper) | Launches persistent homology / topological data analysis; introduces sheaf-based methods for analyzing data over coverings, a direct precursor to SheafDB's consistency checking | HIGH |
| 2009 | SPARQL 1.0 — W3C Recommendation | Standard RDF query language; SheafDB currently supports a subset, not full SPARQL 1.0 | MEDIUM |
| 2010 | Iordanov, "HyperGraphDB" | Hypergraph database extending the directed hypergraph model; earliest explicit "beyond RDF" graph DB with formal underpinnings — shares SheafDB's goal of richer structure | MEDIUM |
| 2012 | SPARQL 1.1 — W3C Recommendation | Adds aggregation, subqueries, property paths, updates; defines the full query surface that SheafDB may eventually target | LOW |
| 2013 | Neo4j 2.0 | Popularizes property graph model with labeled nodes and relationships; establishes the de-facto graph DB paradigm SheafDB differentiates from | LOW |
| 2017 | Angles, "The Property Graph Database Model" (summary) | Formal definition of the property graph model; clarifies its relationship to RDF and highlights limitations (no n-ary edges, no context) that SheafDB addresses | HIGH |
| 2020 | Robinson, "Sheaves and Data" | Applies sheaf theory to consistency of distributed data; introduces sheaf cohomology for measuring inconsistency — directly informs SheafDB's local-global consistency framework | HIGH |
| 2022 | Patterson, "Sheaf Theory in Database Theory" (preprint) | Proposes sheaves as a unifying formalism for database schemas, instances, and queries; most direct theoretical precursor to SheafDB | HIGH |
| 2024 | **SheafDB** (this work) | First implementation of a sheaf-theoretic database with n-ary facts, context-indexed namespaces, and local-global consistency verification | — |
