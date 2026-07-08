# Resource Description Framework (RDF) + Property Graphs (Baseline 2)

## Overview
RDF stores facts as triples (subject, predicate, object). Property graphs extend this with attributes on edges and nodes. These are the standard industry models (used in Neo4j, Amazon Neptune, Apache Jena, RDF4J, GraphDB). SheafDB's KnowledgeGraph engine is an implementation.

## Advantages
- Industry standard — mature, optimized, supported
- SPARQL and Cypher query languages
- RDF supports distributed query (federation via SPARQL endpoints)
- Property graphs support attributes on edges
- Graph databases scale to billions of triples
- Massive optimization ecosystem (indices, caching, query planning)

## Limitations
- **No context representation** — contexts are ad-hoc (named graphs, graph labels)
- No consistency checking (no cocycle condition)
- No global section construction
- High-arity facts require reification (triple → triple about triple)
- Temporal data requires RDF* or reification
- No provenance natively
- SPARQL query optimization is NP-hard

## Comparison to SheafDB
RDF/Property Graphs are the industry baseline. SheafDB extends them with sheaf-theoretic context. SheafDB's KnowledgeGraph engine already provides RDF-like capabilities. The comparison is: SheafDB's sheaf engine vs. standard KG engines on contextual workloads. Benchmark results show SheafDB excels on C8 (consistency), C9 (global sections), and C10 (mixed), while KGs are faster on simple lookup (C1) and path queries (C2).

## Implementation Difficulty: Low (2/5)
Production-ready engines exist. The KnowledgeGraph engine in SheafDB is ∼200 lines.

## Architecture
- RDF: triple store with SP(?)O indices
- Property Graph: adjacency list with edge attributes

## Expected Complexity
- Triple lookup: O(log n) with index
- SPARQL basic graph pattern: O(n^k) worst case for k triple patterns
- Property graph traversal: O(|path| × d_avg) for average degree d
- Insert: O(1) amortized (append + index)

## Verdict
RDF/Property Graphs are the baseline. SheafDB beats them on contextual workloads (C1, C8, C9, C10) and trades off on simple lookup/path queries. No evidence that any RDF enhancement (RDF*, named graphs, quads) matches SheafDB's sheaf-theoretic context capabilities.

## Known RDF Extensions for Context
- Named graphs (RDF 1.1): context as named subgraph — no overlap semantics
- RDF*: reification as first-class — no restriction maps
- RDF streams: temporal RDF — no consistency checking
- Generalized RDF: higher-arity via hyperedges — no global sections

None of these extensions provide SheafDB's full capabilities. The RDF model lacks the algebraic structure (restriction maps, cocycle condition, gluing) that makes SheafDB distinctive.
