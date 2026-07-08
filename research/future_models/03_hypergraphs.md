# Hypergraphs and Typed Hypergraphs

## Overview
A hypergraph generalizes graphs by allowing edges (hyperedges) to connect any number of vertices. A typed hypergraph assigns types to hyperedges. This directly models n-ary semantic facts.

## Advantages
- Directly captures n-ary relations (high-arity facts = hyperedges)
- Typed hyperedges = relation type signatures
- Incidence structure = entity↔fact mapping
- Well-studied in database theory (Codd's relational model as a special case)
- Efficient storage via compressed adjacency representations

## Limitations
- No native context representation
- No consistency checking
- No global section construction
- Temporal and provenance are ad-hoc annotations, not structural
- Hypergraph algorithms (clique, cut, spanning) are NP-hard in general
- No sheaf-like restriction structure

## Comparison to SheafDB
Hypergraphs match SheafDB's high-arity capability but lack context, consistency, provenance, and global sections. For simple fact storage without context requirements, a hypergraph may outperform SheafDB by avoiding sheaf overhead. For contextual workloads, SheafDB dominates.

## Implementation Difficulty: Low (2/5)
Multiple libraries exist for hypergraph storage (HypergraphDB, Baghera). Incidence matrices are well-understood. Basic operations are straightforward.

## Potential Architecture
- Store hyperedges as (id, type, vertices[], attributes)
- Query via incidence matrix operations
- Context as hyperedge attribute (not structural)
- Join via vertex-sharing hyperedge intersection

## Expected Complexity
- Insert: O(1) (append)
- Vertex lookup: O(d) where d = vertex degree
- Pattern match: O(|E|) for unindexed, O(log |E|) with index
- Join: O(|E1| × |E2|) naive, O(|E1| + |E2|) with hash join

## Possible Benchmarks
- High-arity fact storage efficiency
- Pattern matching across typed hyperedges
- Vertex-to-edge navigation
- Join performance vs reified triples
