# Differential Graded Categories and Chain Complex Databases

## Overview
A chain complex is a sequence of abelian groups connected by boundary maps ∂ₙ: Cₙ → Cₙ₋₁ such that ∂ₙ₋₁∘∂ₙ = 0. Differential graded categories categorify this: objects = chain complexes, morphisms = chain maps. For databases: dimension = arity, boundary = projection, ∂² = 0 = consistency condition.

## Advantages
- **∂² = 0 is a consistency condition**: applying projection twice yields zero — no contradictory facts
- Homology = counting inconsistencies (nontrivial cycles)
- Quasi-isomorphism = data equivalence (two DBs with same homologies are equivalent)
- Chain maps = schema transformations
- Natural for temporal data (time direction = chain complex of a cube)
- Provenance via chain homotopy (different ways to prove the same thing)

## Limitations
- Requires abelian group structure (facts must form groups — unnatural for semantic data)
- Grading by dimension = arity suffices but doesn't enrich enough
- No native context representation (like sheaves on a topological space)
- Homology is coarse (many inequivalent complexes have same homology)
- Implementation requires linear algebra with coefficients in a ring
- Boundary maps must satisfy ∂² = 0 — constraints the possible projections

## Comparison to SheafDB
Differential graded categories capture consistency via ∂² = 0 (compare: sheaf cocycle condition). Both detect inconsistency but in different ways. SheafDB's cocycle condition works on overlaps of open sets; chain complexes work on dimensional projection. For semantic data, the sheaf condition is more natural (context overlap matters more than arity projection).

## Implementation Difficulty: Very High (5/5)
Requires linear algebra over arbitrary rings. Chain complex operations (cone, suspension, mapping cone) are standard homological algebra but not implemented in any database context.

## Potential Architecture
- Grade facts by arity (0-ary = entities, 1-ary = properties, 2-ary = relations, ...)
- Define boundary maps: ∂ₙ projects to subsets of arguments
- Enforce ∂² = 0 as constraint on fact addition
- Query = compute homology of a subcomplex
- Temporal = tensor with directed interval chain complex
- Provenance = chain homotopy between computations

## Expected Complexity
- Boundary map storage: O(|Facts| × arity)
- ∂² checking: O(|Facts| × arity²)
- Homology: O(n³) standard, O(n^ω) with fast matrix multiplication
- Chain map: O(|C| × |C'|) for complexes C, C'
- Temporal extension: O(|C| × |T|) for |T| time steps

## Possible Benchmarks
- ∂² = 0 consistency cost vs. sheaf cocycle condition (C8)
- Homology computation for inconsistency detection
- Chain complex storage overhead
- Temporal chain complex efficiency

## Verdict
**Mathematically elegant but practically limited.** The ∂² = 0 constraint enforces a type of consistency but requires group structure on facts — unnatural for semantic data (entity names, predicates don't form groups). Homology detects topological features but at coarse granularity. SheafDB's cocycle condition on context overlaps is more natural for knowledge.
