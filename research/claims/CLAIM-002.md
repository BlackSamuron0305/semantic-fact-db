# CLAIM-002: Cross-engine query equivalence

## Claim
KnowledgeGraph and SheafDatabase produce isomorphic query results for identical inputs and queries.

## Evidence
Verification framework passes all 15 Q1-Q15 queries across all benchmark datasets. The canonical adapter model ensures both engines are tested against the same intermediate representation, eliminating adapter-specific bias.

## Supporting Experiments
All 15 queries tested on both engines across all four benchmarks (micro_1k, relation_dense, deep_context, mixed). Results are bit-identical for simple queries (Q1-Q10) and set-equivalent for complex queries (Q11-Q15). The verification script `verify_equivalence.py` runs as part of CI.

## Supporting Mathematics
Proof of information equivalence via canonical mapping (Paper Theorem 1): the composition SheafDB -> Canonical -> KG and KG -> Canonical -> SheafDB preserves query results for any query expressible in the canonical query language.

## Supporting References
- Paper Section 5 (Verification)
- Paper Theorem 1
- `tests/test_verification.py`

## Paper Section
Section 5 — Verification Framework

## Implementation Modules
- `src/verification/verify_equivalence.py` — Main verification runner
- `src/verification/canonical_model.py` — Canonical intermediate representation
- `src/verification/query_adapter.py` — Query translation layer
- `tests/test_verification.py` — Verification test suite

## Benchmark Figures
Verification test results table showing Q1-Q15 pass/fail; CI pipeline verification badge

## Certainty
HIGH

## Risk if Claim Is False
MEDIUM — the core equivalence claim would be refuted, but individual engines could still be useful independently. Only tested on synthetic data, not real-world workloads.
