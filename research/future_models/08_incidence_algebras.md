# Incidence Algebras on Context Posets

## Overview
Given a poset P (partially ordered set), the incidence algebra assigns to each interval [x,y] the set of functions from [x,y] to a ring. Möbius inversion provides inclusion-exclusion along the poset. For databases: poset = context hierarchy, interval = context transition.

## Advantages
- Context as poset element — natural hierarchy
- Möbius inversion = efficient inclusion-exclusion for context queries
- Zeta function = indicator of comparability
- Convolution = chaining context transitions
- Storage: sparse matrix of interval values
- Simpler than sheaves: no topology, no restriction maps, no gluing

## Limitations
- No consistency checking (no cocycle condition)
- No global section construction
- Only works for posets (sheaves work on any topological space)
- Provenance tracking is ad-hoc (no restriction map structure)
- Möbius inversion requires the poset to be locally finite
- Interval construction is O(|P|²) worst case

## Comparison to SheafDB
Incidence algebras are simpler and likely faster for context-aware queries (Möbius inversion subsumes restriction for posets). However, they lack SheafDB's most powerful features: consistency verification and global section construction. For workloads that don't need these (C1, C2, C3, C4, C6, C7, C10), an incidence algebra database could match or beat SheafDB. For C8 (consistency) and C9 (global section), SheafDB dominates.

## Implementation Difficulty: Medium (3/5)
Incidence algebras are algebraically well-understood. The Möbius function can be precomputed. Sparse matrix libraries handle storage. No topology construction needed.

## Potential Architecture
- Store contexts as a poset (DAG)
- Precompute Möbius function µ(x,y) for all comparable pairs
- Store facts as values on intervals or elements
- Query: zeta transform (sum over intervals) or Möbius inversion
- Temporal: add time as a second poset dimension
- Provenance: annotate interval values with sources

## Expected Complexity
- Poset storage: O(|P|) for elements, O(|P|²) for comparability matrix
- Möbius precomputation: O(|P|³) matrix inversion, or O(|P|²) iterative
- Context query: O(|interval|) via Möbius inversion
- Fact insert: O(1) (append to interval value set)
- Temporal: O(|P| × |T|) with poset product

## Possible Benchmarks
- Möbius precomputation vs. restriction map caching
- Context query: Möbius inversion vs. sheaf restriction chain
- Fact addition with poset maintenance
- Poset dimension (width, height) vs. performance
- Temporal product poset query cost

## Verdict
**Promising alternative for non-consistency workloads.** Incidence algebras match SheafDB's context-awareness with less overhead. The key tradeoff: lose consistency/global sections but gain simplicity and speed. A combined architecture (incidence algebra for fast queries, sheaf for consistency checking) could capture both — but that may be the worst of both worlds in complexity.
