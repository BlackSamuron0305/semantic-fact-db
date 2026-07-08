# Knowledge Compilation (DNNF, OBDD, Sentential Decision Diagrams)

## Overview
Knowledge compilation transforms a knowledge base into a tractable target language (e.g., deterministic decomposable negation normal form — d-DNNF, ordered binary decision diagrams — OBDD, sentential decision diagrams — SDD). The compiled form supports tractable queries (consistency, entailment, model counting, enumeration).

## Advantages
- Tractable query answering (polynomial-time for many query types)
- Exponentially more compact than naive representations
- Deterministic structure enables efficient counting
- SDDs are closed under composition (unlike OBDDs)
- Well-studied for probabilistic reasoning, diagnosis, planning
- Query types: consistency (SAT), entailment, model counting, MPE

## Limitations
- **Compilation is expensive** — can be exponential in worst case
- Compilation must be done offline (no live updates)
- Incremental compilation is hard (small change → full recompile)
- No context representation
- No temporal model
- No provenance tracking
- Variable ordering matters enormously for OBDD/SDD size
- Limited query types (no general join/aggregation)

## Comparison to SheafDB
Knowledge compilation targets different workloads: tractable Boolean reasoning, not contextual semantic retrieval. For SheafDB's C1–C10 benchmarks, compilation-based approaches are ill-suited (no context, no path queries, no global sections). However, for C8 (consistency checking), a compiled SAT solver (d-DNNF) would be extremely fast after compilation — beating SheafDB's iterative consistency check on repeated queries.

## Implementation Difficulty: High (4/5)
Mature libraries exist (cudd for BDDs, Saarland's SDD library, Dsharp for d-DNNF compilation). Integration with a database is novel and requires managing compilation state.

## Potential Architecture
- Compile fact set into SDD (or d-DNNF)
- Query = evaluate on compiled structure (polynomial time)
- Context = variable ordering or subset of variables
- Consistency = satisfiability of compiled theory
- Updates = return to solver (expensive)

## Expected Complexity
- Compilation: O(2^|V|) worst case, O(|V|²) average for well-structured problems
- Query: O(|SDD|) linear in compilation size
- Model counting: O(|SDD|) linear
- Consistency: O(1) (precomputed during compilation)
- Update: O(|SDD|) incremental, O(2^|V|) full recompile

## Possible Benchmarks
- Compilation time vs. fact set size
- Query time on compiled structure vs. direct retrieval
- Incremental update cost
- Variable ordering quality (for decision diagrams)
- Model counting capability (unique to compilation)

## Verdict
Knowledge compilation is a complement, not a competitor to SheafDB. It provides fast Boolean query capabilities (consistency, entailment, counting) after expensive compilation. For SheafDB, a compilation-based consistency checker could accelerate C8: compile the fact set offline, check consistency instantly. Not viable as a general-purpose semantic database due to restricted query types and expensive updates.
