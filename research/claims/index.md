# SheafDB Claims Index

| ID | Title | Certainty | Evidence Status | Paper Section | Risk |
|---|---|---|---|---|---|
| CLAIM-001 | Sheaf theory provides rigorous foundations for semantic facts | HIGH | EXISTS | Sections 2-4 | HIGH |
| CLAIM-002 | Cross-engine query equivalence | HIGH | EXISTS | Section 5 | MEDIUM |
| CLAIM-003 | Sheaf insertion O(d) amortized | MEDIUM | EXISTS | Sections 4.1, 6.2 | MEDIUM |
| CLAIM-004 | Context-indexed storage avoids join explosion | MEDIUM | EXISTS | Sections 3.2, 6.3 | MEDIUM |
| CLAIM-005 | SheafDB preferred for contextual queries | HIGH | EXISTS | Sections 6.4 | HIGH |
| CLAIM-006 | KG preferred for non-contextual dense graphs | MEDIUM | PARTIAL | Sections 3.3, 6.3 | MEDIUM |
| CLAIM-007 | Sheaf gluing is correct | LOW | EXISTS | Sections 4.2, Appendix A | MEDIUM |
| CLAIM-008 | Canonical mapping is lossless | LOW | EXISTS | Sections 5.1, 5.2 | HIGH |
| CLAIM-009 | Sheaf storage reduces memory for n-ary facts | MEDIUM | EXISTS | Sections 3.2, 6.5 | MEDIUM |
| CLAIM-010 | Query execution is deterministic | LOW | EXISTS | Section 5.3 | LOW |
| CLAIM-011 | Sheaf consistency checking detects anomalies | LOW | EXISTS | Section 4.3 | MEDIUM |
| CLAIM-012 | Both engines scale linearly with dataset size | MEDIUM | EXISTS | Section 6.6 | MEDIUM |
| CLAIM-013 | No prior complete sheaf-based database exists | HIGH | EXISTS | Section 7 | HIGH |
| CLAIM-014 | Context poset with Alexandrov topology is novel | HIGH | EXISTS | Sections 2.1, 2.2 | HIGH |
| CLAIM-015 | Benchmark framework supports fair cross-engine comparison | MEDIUM | EXISTS | Sections 5, 6.1 | MEDIUM |

**Summary:**
- HIGH certainty: 5 claims
- MEDIUM certainty: 6 claims
- LOW certainty: 4 claims
- Evidence EXISTS: 14 claims
- Evidence PARTIAL: 1 claim (CLAIM-006)
- HIGH risk: 5 claims
- MEDIUM risk: 9 claims
- LOW risk: 1 claim

**Key risk concentrations:**
- Theoretical novelty: CLAIM-001, CLAIM-013, CLAIM-014 are all HIGH risk — the paper's novelty hinges on these
- Core methodology: CLAIM-008 is HIGH risk — the verification framework depends on lossless mapping
- Performance narrative: CLAIM-005 is HIGH risk — the primary performance claim may not be clearly demonstrated

**Status key:**
- EXISTS: Evidence is documented and available
- PARTIAL: Some evidence exists but is incomplete
- MISSING: No evidence yet

**Honest scope note:** The benchmark framework defines 5 engine adapters (KG, Sheaf, Jena, Blazegraph, Neo4j) but only 2 (KG, Sheaf) have working implementations. The Jena adapter has partial rdflib support; Blazegraph and Neo4j are stubs. All cross-engine comparisons in the paper are between KG and Sheaf only.
