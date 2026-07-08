# Concept Lattices and Formal Concept Analysis (FCA)

## Overview
FCA identifies formal concepts from a formal context (objects × attributes matrix). A concept is a maximal set of objects sharing a maximal set of attributes. The concept lattice organizes these by generality. For databases: facts = context table, concepts = natural entity groupings.

## Advantages
- Automatic hierarchy discovery from data
- Concept lattice = natural taxonomy of entity groups
- Implications = attribute dependencies (∀a, b: a → b)
- Well-studied with efficient algorithms (Ganter's Next Closure, Lindig)
- Duality between objects and attributes = entity↔property symmetry

## Limitations
- Computation is **exponential** in worst case (|Concepts| ≤ 2^min(|O|,|A|))
- Static — adding new objects/attributes can rebuild the entire lattice
- No query semantics — FCA is an analysis tool
- No context representation (formal context is flat)
- No temporal/provenance/consistency
- Concept lattice is not a database; it's a discovered structure

## Comparison to SheafDB
FCA is fundamentally different: it discovers structure from a flat matrix; SheafDB uses predefined context. FCA excels at taxonomy building but cannot serve as a general-purpose semantic database. The concept lattice is a poset — could be used as the context poset for an incidence algebra or sheaf, providing automated topology discovery.

## Implementation Difficulty: Medium (3/5)
FCA algorithms are well-known and moderately efficient for sparse matrices. Next Closure is O(|Concepts| × |A|²). Scaling beyond 10⁵ objects/attributes is challenging.

## Potential Architecture (Combined FCA + Sheaf)
- Build formal context from entity × attribute matrix
- Compute concept lattice via Next Closure
- Use concept lattice as the context poset for a sheaf or incidence algebra
- Store facts on concept intents (shared attributes)
- Query = navigate the concept lattice and inspect facts

## Expected Complexity
- Lattice construction: O(|C| × |A|²) for |C| concepts, |A| attributes
- Concept lookup: O(log |C|)
- Fact insert: may rebuild part of lattice
- Query: traverse lattice via order relations

## Possible Benchmarks
- Lattice construction time vs. data size
- Concept discovery quality (precision/recall)
- Lattice maintenance under insertions
- Query efficiency over concept-structured data

## Verdict
FCA cannot replace SheafDB as a database, but could provide automated context topology discovery — similar to TDA's mapper. The concept lattice gives a natural poset for sheaf or incidence algebra construction. Most promising as a SheafDB enhancement rather than an alternative.
