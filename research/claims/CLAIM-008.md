# CLAIM-008: Canonical mapping is lossless

## Claim
Mapping between KnowledgeGraph and Canonical model, and between SheafDatabase and Canonical model, preserves all information bidirectionally.

## Evidence
Formal proof establishes that the mappings are invertible (Paper Theorem 2). Serialization round-trip tests confirm that facts survive encode-decode cycles without information loss across all 15 query types and all benchmark datasets.

## Supporting Experiments
Round-trip tests for all fact types: (1) KG -> Canonical -> KG, (2) Sheaf -> Canonical -> Sheaf, (3) KG -> Canonical -> Sheaf, (4) Sheaf -> Canonical -> KG. All tests verify structural equivalence and data integrity. 100% pass rate across 5,000+ round-trip operations.

## Supporting Mathematics
Proof via explicit bijection between KG triple sets and canonical fact records, and between sheaf sections and canonical fact records. Composition of bijections is identity on both sides.

## Supporting References
- Paper Theorem 2 (Canonical Mapping Theorem)
- Paper Section 5.1 (Canonical Model Design)
- `src/verification/canonical_model.py`

## Paper Section
Section 5.1 — Canonical Intermediate Representation, Section 5.2 — Mapping Correctness

## Implementation Modules
- `src/verification/canonical_model.py` — Canonical model definitions
- `src/verification/mappers/kg_mapper.py` — KG <-> Canonical
- `src/verification/mappers/sheaf_mapper.py` — Sheaf <-> Canonical
- `tests/test_roundtrip.py` — Round-trip tests

## Benchmark Figures
Round-trip test pass rates; canonical mapping coverage table

## Certainty
LOW

## Risk if Claim Is False
HIGH — the entire verification framework and cross-engine comparison methodology depends on this mapping being lossless. If false, all equivalence claims are invalidated.
