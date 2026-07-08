# Relation Algebras (Tarski)

## Overview
A relation algebra is an algebraic structure (Booleans + composition + converse + identity) for binary relations. It axiomatizes the calculus of binary relations. For databases: relations = facts, composition = join, converse = inverse.

## Advantages
- Rich algebraic query language: composition, union, intersection, complement, transitive closure
- Directly models binary relations — natural for triples
- Tarski's axiomatization provides equational reasoning for query optimization
- Well-studied in algebraic logic and database theory
- Can express path queries, reachability, constraint satisfaction

## Limitations
- Binary only — generalizing to n-ary requires encoding (tuples → binary relations)
- No context representation
- No temporal model (time must be encoded as a relation)
- No provenance tracking
- No consistency checking
- Representing n-ary facts as binary decompositions causes information loss

## Comparison to SheafDB
Relation algebras are a query algebra, not a storage model. SheafDB uses relational algebra internally for stalk storage. The relation algebra adds no capability beyond what relational databases already provide, and lacks SheafDB's context, consistency, and provenance features.

## Implementation Difficulty: Low (2/5)
Relational databases implement much of relation algebra. Relational algebra optimization is mature (40+ years of research).

## Potential Architecture
- Store binary relations as tables
- Query via relation algebra operations
- Context as an additional relation column (not structural)
- Optimization via Tarski's algebraic laws

## Expected Complexity
- Binary relation storage: O(n)
- Composition: O(n²) naive, O(n log n) indexed
- Transitive closure: O(n³) Floyd-Warshall, O(n(m+n)) incremental
- Complement: O(|U|) where U is universe

## Possible Benchmarks
- Composition chain performance
- Transitive closure over large relations
- Algebraic optimization effectiveness
- Expressiveness comparison for real queries

## Verdict
Relation algebras are a query optimization technique for the relational core already used in SheafDB (stalk storage). They do not provide a database architecture that competes with SheafDB.
