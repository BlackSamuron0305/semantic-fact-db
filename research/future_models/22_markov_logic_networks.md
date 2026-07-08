# Probabilistic Graphical Model Database / Markov Logic Networks

## Overview
Markov Logic Networks (MLNs) are weighted first-order formulas treated as soft constraints in a Markov network. Tuples = ground atoms, weights = confidence/importance. Query = probabilistic inference over the Markov network.

## Advantages
- Uncertainty handling via probabilistic weights
- Soft consistency (contradictions reduce probability but don't break the model)
- First-order formulas as templates for inference
- Well-studied with mature tools (Alchemy, Tuffy, RockIt, DeepDive)
- Inference can incorporate domain knowledge
- Learning from data (weight learning, structure learning)

## Limitations
- **Inference is #P-complete** in the worst case
- Markov chain Monte Carlo is slow for large databases
- No exact answers (only probabilities)
- No context representation
- No temporal model (must be encoded)
- No explicit provenance
- Weight learning requires labeled data
- Grounding first-order formulas creates large networks

## Comparison to SheafDB
MLNs solve a different problem: probabilistic inference over weighted formulas. SheafDB solves exact contextual retrieval. MLNs tolerate inconsistency (soft constraints) while SheafDB detects it (cocycle condition). For domains requiring exact answers (the semantic database use case), MLNs are inapplicable. For uncertain knowledge bases, MLNs could complement SheafDB's exact consistency.

## Implementation Difficulty: Medium-High (3.5/5)
Mature tools exist (Tuffy, RockIt) but scale poorly. DeepDive uses PostgreSQL for grounding.

## Expected Complexity
- Grounding: O(|Formulas| × |Atoms|^arity) — exponential
- Inference (MC-SAT): O(iterations × |Ground network|)
- Weight learning: O(epochs × inference)

## Verdict
MLNs serve a complementary need (probabilistic reasoning) to SheafDB (exact contextual retrieval). Not a replacement. If exact consistency constraints are relaxed, MLNs could be part of a hybrid architecture.
