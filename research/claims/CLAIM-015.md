# CLAIM-015: Benchmark framework supports fair cross-engine comparison

## Claim
The canonical model enables unbiased comparison between fundamentally different representations (sheaf sections vs RDF triples).

## Evidence
Benchmark design separates engine-specific storage from the canonical intermediate representation. Each benchmark dataset is defined in canonical form, then automatically converted to each engine's native format. Query results are compared in canonical space. No engine receives data in its native format natively; both go through the adapter.

## Supporting Experiments
All 15 queries produce equivalent results across engines (CLAIM-002). Adapters are symmetric: KG Canonical uses the same code path as Canonical KG. Dataset loading time is excluded from benchmark timing to avoid penalizing conversion overhead.

## Supporting Mathematics
Theorem 2 (Canonical Mapping Theorem) establishes the mapping is a bijection, so neither engine's adapter introduces information asymmetry.

## Supporting References
- Paper Section 5 (Verification Framework)
- Paper Section 6 (Benchmark Design)
- `src/verification/canonical_model.py`

## Paper Section
Section 5 — Verification Framework, Section 6.1 — Benchmark Methodology

## Implementation Modules
- `src/verification/benchmark_runner.py` — Benchmark execution framework
- `src/verification/mappers/kg_mapper.py` — KG adapter
- `src/verification/mappers/sheaf_mapper.py` — Sheaf adapter
- `src/verification/dataset_converter.py` — Dataset conversion

## Benchmark Figures
Benchmark methodology diagram; adapter symmetry verification results

## Certainty
MEDIUM

## Risk if Claim Is False
MEDIUM — adapters may not be perfectly neutral. Implementation bias could favor one engine (e.g., adapter using engine-specific optimizations). Reviewers may question whether the same developer implementing both adapters introduces unconscious bias.
