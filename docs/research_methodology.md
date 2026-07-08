# Research Methodology

## Research Workflow

1. **Literature review → Identify gap**
   - Survey existing work in category-theoretic databases, sheaf theory in CS, and RDF/SPARQL systems
   - Identify underexplored areas (incremental sheaf computation, lazy restriction maps, etc.)
   - Document closest prior work for each claimed contribution

2. **Formal model definition → Theorems and proofs**
   - Define sheaf-theoretic data model (context lattice, sections, restriction maps)
   - State theorems: gluing correctness, query equivalence, complexity bounds
   - Develop proofs in `research/proofs/` with formal notation
   - Verify proofs through review simulation (see Quality Gates)

3. **Implementation → SheafDB (sheaf path) + KG (baseline path)**
   - Implement sheaf path: context lattice → sheaf construction → gluing → sheaf query engine
   - Implement KG baseline: RDF store using the same fact representation
   - Both paths share: fact ingestion, canonical model, benchmark harness
   - Located in `src/sheaf_db/` and `src/kg/`

4. **Cross-engine verification → Canonical model, query equivalence**
   - Both engines process identical facts and queries
   - Cross-engine query equivalence checked via result-set comparison
   - Canonical model stored in `research/mappings/` for reproducibility
   - Stored in `results/` per experimental run

5. **Benchmarking → Standardized workloads, system metrics**
   - Synthetic benchmarks: varying fact count, query complexity, context structure
   - Real-world datasets: target Wikidata, DBpedia subsets
   - System metrics: CPU time, memory, query latency, gluing cost
   - All runs recorded with seed, timestamp, system info, Git commit hash

6. **Analysis → Theoretical complexity + empirical evaluation**
   - Compare asymptotic bounds (sheaf vs KG for each query type)
   - Empirical validation: measure actual vs predicted scaling
   - Identify bottlenecks and optimization opportunities
   - Record in `research/notes/` and `results/`

7. **Paper writing → Claims with evidence tracking**
   - Every claim assigned a CLAIM-NNN identifier
   - Each claim linked to evidence (benchmark result, theorem, citation)
   - Evidence status tracked: EXISTS / PARTIAL / MISSING
   - Claims without evidence removed before submission

## Evidence Requirements

| Claim Type | Evidence Required |
|---|---|
| Theoretical | Formal proof or citation to known theorem |
| Performance | Benchmark results (mean, std dev, number of runs, random seed) |
| Novelty | Closest prior work cited with explicit difference explained |
| Architectural | Link to relevant source files and design documents |

Every claim must have a unique ID in `research/claims/`.

## Novelty Validation Process

1. For every feature, classify into one of:
   - **KNOWN** — exists in prior work as described
   - **KNOWN-NOT-IMPLEMENTED** — known but not implemented in any system
   - **RESEARCH-PROTOTYPE** — exists only in academic prototypes
   - **COMMERCIAL** — available in commercial systems
   - **NOVEL** — no prior work found

2. Document the closest prior work for each feature with full citation.

3. If classification is uncertain, mark it as **LOW** certainty and document what additional evidence is needed.

4. Never claim novelty without literature evidence. A literature gap is a hypothesis, not a finding.

5. Before paper submission: re-validate all novelty claims against the latest literature (last 6 months).

## Claim Verification

1. Every claim in a paper must have a CLAIM-NNN entry in `research/claims/`.

2. Every claim must have an Evidence rating:
   - **EXISTS** — supporting evidence is complete and documented
   - **PARTIAL** — some evidence exists but gaps remain
   - **MISSING** — no supporting evidence

3. If Evidence = MISSING, the claim must be removed from the paper.

4. Before every paper revision: re-check all claim evidence, updating ratings as needed.

## Literature Maintenance

1. `paper/bibliography.bib` and `research/literature/references.bib` must stay in sync. Any change to one must be mirrored in the other.

2. New related works discovered during review must be added to both bibliography files immediately.

3. Literature taxonomy in `research/literature/` must be updated when new categories emerge (e.g., incremental sheaves, distributed category theory).

## Quality Gates (Pre-Submission Checklist)

See `research/quality_gates.md` for the complete quality gate checklist. The project MUST refuse to mark itself as "research complete" if any gate condition is unmet.
