# Simplicial Complexes and Cell Complexes

## Overview
A simplicial complex is a set of simplices (points, edges, triangles, tetrahedra...) closed under taking faces. A cell complex generalizes this by allowing cells of different shapes. These are classical algebraic topology structures.

## Advantages
- Dimension = arity (k-simplex = k+1-ary fact)
- Face maps = projection to subsets of arguments
- Boundary operator = fact decomposition
- Well-defined homology = counting "holes" in knowledge
- CW complexes allow heterogeneous cell types (different arities)
- Efficient algorithms for low dimensions

## Limitations
- Simplicial complexes require downward closure (all subsets of a fact are also facts) — artificial for knowledge representation
- CW complexes relax this but complicate the algebra
- No native context representation
- No consistency checking
- No global section construction
- Temporal/provenance are ad-hoc
- Homology is interesting theoretically but rarely useful practically for databases

## Comparison to SheafDB
Simplicial complexes provide a natural home for high-arity facts via dimension. The face maps are analogous to restriction maps but in the opposite direction (projecting to subsets rather than specializing contexts). SheafDB's sheaves on a topological space are strictly more general than simplicial complexes.

## Implementation Difficulty: Medium (3/5)
Well-studied in computational topology (GUDHI, Dionysus libraries exist). Basic operations (filtration, homology) have efficient implementations. Storage via simplex trees or Hasse diagrams.

## Potential Architecture
- Store simplices (facts) in a simplex tree
- Face maps = projection to subsets of arguments
- Query = traversal of the Hasse diagram
- Filtration = ordering by context, time, or confidence

## Expected Complexity
- Insert: O(k) for k-face simplex (need all faces)
- Face lookup: O(1) with Hasse diagram
- Homology: O(n³) worst case for persistence
- Boundary computation: O(1) per face

## Possible Benchmarks
- Face map traversal cost
- Simplex insertion with closure
- Filtration construction time
- Homology group computation (C1 persistence)
