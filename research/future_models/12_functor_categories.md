# Functor Categories

## Overview
For categories C and D, the functor category [C, D] has functors F: C → D as objects and natural transformations as morphisms. For databases: C = schema (context category), D = Set (the category of sets). [C, Set] is a presheaf category.

## Advantages
- Schema migration = change of base C → C'
- Natural transformation = query across schemas
- Yoneda lemma = object is represented by its hom-functor (entity = its relationships)
- Kan extension = universal query construction (join, aggregation, grouping)
- Most general categorical database model (CQL, AQL based on this)
- SheafDB's presheaves = [Open(X)ᵒᵖ, Set] (special case)

## Limitations
- Extremely abstract — hard to implement efficiently
- Schema category C must be predefined
- Kan extensions are (co)limit computations = expensive
- Yoneda embedding is O(|C| × |Ob|) — large
- No built-in temporal or provenance (must be encoded in C)
- Performance depends on category size and shape

## Comparison to SheafDB
SheafDB's presheaf on a finite topological space is a functor category [Open(X)ᵒᵖ, Set]. General functor categories add schema migration (change of base category) but at significant implementation cost. SheafDB already uses the most important functor category for semantics. Generalizing to arbitrary schema categories adds complexity without clear benefit for the current use case.

## Implementation Difficulty: Very High (5/5)
Only known implementations are research prototypes (CQL, AQL) with limited distribution and performance.

## Architecture
Functor category database = (C, F) where F: C → Set is a functor. Schema = C, instances = F(c) for objects c, relationships = F(f) for morphisms f. Query = limit/colimit computation.

## Expected Complexity
- Schema definition: O(|C|) (objects + morphisms)
- Instance lookup: O(log Σ|F(c)|)
- Kan extension: O(|C| × Σ|F(c)|) worst case
- Natural transformation (query): O(|C| × |C'|) for schema migration

## Possible Benchmarks
- Schema migration cost
- Yoneda embedding construction time
- Kan extension computation for queries

## Verdict
Functor categories are the most general categorical framework for databases. SheafDB is already a functor category. Generalization to arbitrary C adds schema migration complexity not required by the current problem. No clear path to beating SheafDB on contextual semantic queries.
