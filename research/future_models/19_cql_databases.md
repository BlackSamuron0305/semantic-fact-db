# Categorical Query Language (CQL / AQL) — Functorial Data Migration

## Overview
CQL/AQL (Spivak, Wisnesky, Schultz) implement categorical data migration: databases as functors C → Set, queries as (co)limits, schema migration via Kan extensions. A commercial implementation exists (CategoricalQueryLanguage, now CQL).

## Advantages
- Schema migration = change of base — provably correct via adjunctions
- Query = universal construction (limit/colimit) — declarative
- Pushforward/pullback = data migration between schemas
- CoSpan composition = multi-schema integration
- Proven correctness through category theory
- Commercial implementation available
- Handles n-ary relations via product types

## Limitations
- Limited to the relational model (Set-valued functors)
- No context structure — schemas are categories, not topological spaces
- No consistency checking (cocycle condition)
- No global section construction
- No temporal or provenance natively
- Kan extensions are expensive (O(|C| × |D|) for small categories)
- CQL implementation is a research prototype — not production-grade

## Comparison to SheafDB
CQL is the closest competitor conceptually. Both use category theory for databases. Key difference: CQL uses arbitrary categories as schemas and Set-valued functors as instances, focusing on schema migration. SheafDB restricts to finite topological spaces (a specific kind of category) and adds sheaf-specific operations (restriction, consistency, gluing). CQL handles schema evolution; SheafDB handles context-aware querying. They solve different problems.

For contextual semantic queries (C1–C10), CQL provides no advantage — it lacks context as a structural concept. SheafDB's sheaf-on-a-topology directly captures context in a way CQL cannot without encoding it as a schema (which loses the restriction structure).

## Implementation Difficulty: High (4/5)
CQL provides a reference implementation (Java). Extending it for sheaf semantics would require significant modification.

## Architecture
- Schema = category C
- Instance = functor F: C → Set
- Query = limit/colimit in Set^C
- Migration = left/right Kan extension along functor
- Schema integration = coSpan/Cospan composition

## Expected Complexity
- Instance storage: O(Σ|F(c)|) sum over objects
- Pullback: O(|C| × |C'|) for C → C'
- Limit computation: O(|C| × Σ|F(c)|)
- Kan extension: O(|C| × |D|) exponential for left Kan

## Verdict
CQL is not a SheafDB competitor — it targets schema migration, not context-aware querying. The category-theoretic foundations are shared but the application domains differ. CQL's schema migration could be useful for SheafDB's context topology evolution, but doesn't replace SheafDB for contextual semantic storage.
