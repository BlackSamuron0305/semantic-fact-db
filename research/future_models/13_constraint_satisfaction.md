# Constraint Satisfaction Graphs / Graphical Models

## Overview
A constraint satisfaction problem (CSP) is a triple (V, D, C) where V are variables, D are domains, C are constraints. A graphical model (factor graph, Bayesian network, Markov random field) augments CSP with probability distributions. For databases: facts = constraints, query = constraint propagation.

## Advantages
- Native consistency checking (arc consistency, i-consistency)
- Uncertainty handling via probability distributions
- Query = inference (belief propagation, variable elimination)
- Constraint propagation = query answering with pruning
- Factor graphs naturally represent high-arity relationships
- Well-studied with efficient algorithms (DPLL, AC-3, junction tree)

## Limitations
- No context representation (context = subproblem, not structural)
- Variable elimination is NP-hard in treewidth
- No global section construction
- No temporal model
- Constraint satisfaction is #P-complete in general
- Junction tree construction is O(n^w) where w = treewidth
- Provenance is ad-hoc

## Comparison to SheafDB
Constraint graphs and sheaves are surprisingly related: a sheaf's consistency condition (cocycle condition) is analogous to constraint propagation on an overlap graph. Constraint satisfaction is NP-complete; sheaf consistency checking (on a good topology) can be more tractable. CSPs have no structural context representation — this is the main advantage SheafDB holds.

## Implementation Difficulty: High (4/5)
CSP libraries exist (Google OR-Tools, Choco, Gecode) but integrating into a database requires adapting inference algorithms for query answering rather than pure satisfaction.

## Potential Architecture
- Variables = entity/relation slots
- Domains = possible values
- Constraints = facts restricting valid combinations
- Query = variable elimination on subproblem
- Consistency = arc consistency check

## Expected Complexity
- Fact insert: O(1) (add constraint)
- Arc consistency: O(n²d³) for n vars, d domain size
- Variable elimination: O(n × w × d^w) for treewidth w
- Marginal inference: O(n × 2^w) with junction tree

## Possible Benchmarks
- Constraint propagation for fact retrieval
- Consistency checking cost vs. sheaf cohomology
- Treewidth computation scalability
- Uncertainty handling quality

## Verdict
Constraint satisfaction models are not a replacement for SheafDB — they solve a different problem (satisfaction vs. storage and retrieval). The connection between constraint propagation and sheaf consistency is mathematically interesting but does not yield a better database architecture. A CSP-style consistency checker could enhance SheafDB's C8 (consistency checking) implementation.
