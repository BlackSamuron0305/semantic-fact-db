# Paper Issues — Detailed Audit

**Date:** 2026-07-08  
**Scope:** All 30 issues identified across the paper LaTeX source, result tables, figures,
benchmark code, and metadata files. Issues are grouped by category and ordered by severity
(blocking → major → minor).

---

## Category A — Unverified / Projected Claims
*These are the highest-severity issues. A reviewer who catches any of them can reject the
paper outright on grounds of fabricated or unsupported data.*

---

### Issue 1 — C10 flagship section claims a "projected 3–10× speedup" that contradicts measured data

**File:** `paper/sections/11_mixed_flagship.tex`, line 23  
**Severity:** Blocking — desk-reject risk

**Exact problematic text:**
```
The end-to-end SheafDB pipeline is projected to achieve a 3--10$\times$ speedup
over the equivalent SPARQL pipeline at 100K-fact scale, with the gap widening at
larger scales and deeper provenance chains.
```

**Why it's wrong:**  
The actual `bench_10k` results (10K facts, the largest scale tested) show SheafDB is
**slower** than KG on general queries: SheafDB mean 0.22–0.29 ms vs. KG 0.15–0.22 ms
(ratio 1.3–1.5× in KG's favour). The new `evaluation.tex` correctly reports that GLOBAL
full-scan queries are up to 1405× slower on SheafDB at 10K facts. The C10 section claims
the opposite and at a scale (100K) that was never benchmarked. "Projected" performance
numbers are not acceptable in an empirical systems paper.

**What it should say:**  
The C10 section must be rewritten around measured results. The correct story is that
SheafDB's LOOKUP advantage (30×) applies to the individual entity-centric stages of the
pipeline, but that a full multi-stage pipeline involving global scans would be dominated
by SheafDB's current GLOBAL overhead. Either (a) replace the section with the measured
LOOKUP/GLOBAL breakdown from `evaluation.tex`, or (b) mark C10 explicitly as "future
work — not yet implemented end-to-end" and remove the projected speedup claim.

---

### Issue 2 — C10 placeholder table and non-existent figure

**Files:** `paper/tables/mixed_flagship_results.tex`, `paper/sections/11_mixed_flagship.tex` line 27–32  
**Severity:** Blocking — visible in compiled PDF

**Exact problematic content in the table file:**
```latex
\multicolumn{4}{c}{\emph{Run benchmarks to populate}} \\
```

**Exact figure reference in the section:**
```latex
\includegraphics{figures/flagship_breakdown.pdf}
```

**Why it's wrong:**  
The table contains a literal placeholder message that will appear verbatim in the compiled
PDF. The figure `figures/flagship_breakdown.pdf` does not exist in `paper/figures/`
(confirmed by directory listing). LaTeX will either fail to compile or produce a broken
figure box. Both are visible to any reviewer who opens the PDF.

**What to do:**  
Remove the `\input{tables/mixed_flagship_results.tex}` call and the figure block from
`11_mixed_flagship.tex` until real results exist. Replace with a note such as
"End-to-end pipeline benchmarks are reserved for future work; per-stage LOOKUP/GLOBAL
results appear in Section~\ref{sec:evaluation}."

---

### Issue 3 — §07 high-arity "Expected outcomes" paragraph projects unmeasured results

**File:** `paper/sections/07_high_arity.tex`, lines 13–16  
**Severity:** Blocking

**Exact problematic text:**
```
Workloads C3 (point-lookup) and C4 (range-scan) are evaluated at arity 3, 5, 8, and 12,
each at scale 1K, 10K, 100K, and 1M facts. Both uniformly random and Zipf-distributed
attribute values are tested. ...
SheafDB lookup latency should remain essentially flat across arity ($O(1)$), while KG
systems degrade linearly ($O(a)$) due to the $2a+1$ triple expansion. The gap widens with
scale: at arity 12 and 1M facts, SheafDB is projected to outperform reification-based
stores by a factor proportional to $a$.
```

**Why it's wrong:**  
Two separate problems: (1) the experimental setup claims tests at 100K and 1M facts — the
actual benchmark was run at max 10K facts; (2) the "expected outcomes" paragraph uses
future tense and the word "projected", presenting hypothesis as result. No arity-sweep
benchmark output exists in `results/`. The figure `figures/high_arity_scaling.pdf` is
also missing.

**What to do:**  
(a) Change the setup paragraph to state the actual tested scales (1K and 10K).  
(b) Replace the "Expected outcomes" paragraph with a "Note: high-arity scaling experiments
are ongoing; O(1) vs O(a) theoretical analysis appears in Section~\ref{sec:complexity}."  
(c) Remove or stub the `\includegraphics{figures/high_arity_scaling.pdf}` reference.

---

### Issue 4 — §08 temporal/provenance section claims unmeasured 1M-fact experiments and N-fold speedup

**File:** `paper/sections/08_temporal_provenance.tex`, lines 8 and 15–16  
**Severity:** Blocking

**Exact problematic text (line 8):**
```
SheafDB executes a single pass over the interval index ... yielding an expected $N$-fold
reduction in query overhead.
```

**Exact problematic text (lines 15–16):**
```
Workloads C5 (temporal point-query), C6 (sliding-window aggregation), and C7 (provenance
chain traversal) are evaluated at scale 1K--1M facts with interval widths drawn from
uniform and exponential distributions. Provenance chain depth ranges from 1 to 100 steps.
```

**Why it's wrong:**  
The `results/` directory contains no temporal or provenance benchmark output files. The
table `paper/tables/temporal_provenance_results.tex` is a placeholder. The 1M-fact claim
is false (max tested scale is 10K), and "expected N-fold reduction" is a theoretical claim
presented as an empirical result. The figure `figures/temporal_performance.pdf` does not
exist.

**What to do:**  
Replace the setup paragraph with the actual tested scale. Replace "expected N-fold
reduction" with the measured data if available, or move the claim to the complexity
section as a theoretical bound. Remove the missing figure reference.

---

### Issue 5 — §10 ablation section is entirely speculative

**File:** `paper/sections/10_ablation.tex`, lines 34–35 and throughout  
**Severity:** Blocking

**Exact problematic text:**
```
\paragraph{Expected insights.}
Preliminary analysis indicates that interval indexing (C5--C6), cocycle caching (C8), and
reification bypass (C3--C4) are the three highest-impact modules, together accounting for
more than 60\% of the performance gap between Minimal and Default profiles. Pairwise
sweeps reveal a synergistic effect between morphism inlining and restriction-map
memoization that yields super-linear speedups on provenance workloads (C7).
```

**Why it's wrong:**  
The entire ablation methodology described — 33 modules, 528 pairwise sweeps, 1000 random
configuration samples, 10 continuous parameter sweeps across 9 scalability dimensions —
was never executed. "Preliminary analysis indicates" and "Pairwise sweeps reveal" present
invented conclusions as measured results. The two figures (`ablation_heatmap.pdf`,
`sensitivity_radar.pdf`) and the table (`ablation_summary.tex`) are all placeholders or
non-existent. The 33-module optimization framework described in this section is not fully
implemented in the codebase (the optimizer in `src/sfdb/optimizer/optimizer.py` exists
but does not expose 33 independently toggleable modules matching this description).

**What to do:**  
Either (a) run a real, scoped ablation (e.g., three configurations: no index, stalk index
only, full optimizer) and report those numbers, or (b) remove the ablation section
entirely and move the optimization framework description to a future work subsection.
Do not present the "33-module" framing as an empirical study.

---

## Category B — Placeholder Tables (9 files)

### Issue 6 — Nine result tables contain literal placeholder content

**Files:** All in `paper/tables/`  
**Severity:** Major — compiled PDF shows placeholder text

The following table files all contain the same boilerplate placeholder body that was
auto-generated by `scripts/generate_paper.py` and never populated with real data:

| Table file | Referenced in section |
|---|---|
| `ablation_summary.tex` | `10_ablation.tex` |
| `cache_stats.tex` | Unknown (likely `experimental_setup.tex`) |
| `consistency_results.tex` | `09_consistency_global_sections.tex` |
| `dataset_stats.tex` | Unknown |
| `high_arity_results.tex` | `07_high_arity.tex` |
| `mixed_flagship_results.tex` | `11_mixed_flagship.tex` |
| `storage.tex` | Unknown |
| `temporal_provenance_results.tex` | `08_temporal_provenance.tex` |
| `workloads.tex` | `06_contextual_workloads.tex` |

**Exact placeholder content in each:**
```latex
\multicolumn{4}{c}{\emph{Run benchmarks to populate}} \\
```

**Why it's wrong:**  
Any reviewer who compiles the paper sees "Run benchmarks to populate" in the PDF. This
immediately signals the paper was submitted before being finished.

**What to do:**  
For each table, either (a) run the corresponding benchmark and populate from real results,
or (b) remove the `\input{}` call from the section file and replace with a prose sentence
reporting the key numbers already present in `results/bench_10k.md` and `evaluation.tex`.
The `consistency_results` and `high_arity_results` tables may require new benchmark runs.

---

## Category C — Missing Figures

### Issue 7 — Five figures are referenced in the paper but do not exist on disk

**Location:** `paper/figures/` (confirmed via directory listing)  
**Severity:** Major — causes LaTeX compilation failure or broken figure boxes

| Figure filename | Referenced in section | Status |
|---|---|---|
| `flagship_breakdown.pdf` | `11_mixed_flagship.tex` | Missing |
| `high_arity_scaling.pdf` | `07_high_arity.tex` | Missing |
| `temporal_performance.pdf` | `08_temporal_provenance.tex` | Missing |
| `global_section_scaling.pdf` | `09_consistency_global_sections.tex` | Missing |
| `ablation_heatmap.pdf` | `10_ablation.tex` | Missing |
| `sensitivity_radar.pdf` | `10_ablation.tex` | Missing |

**Figures that DO exist (for reference):**  
`architecture.pdf`, `cdf.pdf`, `latency.pdf`, `memory.pdf`, `restriction.pdf`,
`scalability.pdf`, `scaling.pdf`, `speedup.pdf`, `storage.pdf`, `throughput.pdf`,
`topology.pdf`

**Why it's wrong:**  
When LaTeX includes a non-existent PDF with `\includegraphics`, it either errors out
(pdflatex) or produces a broken image box. The paper cannot be compiled cleanly.

**What to do:**  
For each missing figure: either generate it from measured benchmark data using
`scripts/generate_paper.py`, or remove the `\begin{figure}...\end{figure}` block from
the section and replace the visual with a prose description.

---

## Category D — Cross-Reference Errors

### Issue 8 — §06 references non-existent label `sec:results`

**File:** `paper/sections/06_contextual_workloads.tex`, line 54  
**Severity:** Major — produces `??` in compiled PDF

**Exact problematic text:**
```latex
Section~\ref{sec:results} reports the per-workload speedup and equivalence status.
```

**Why it's wrong:**  
No section in the paper has the label `\label{sec:results}`. The evaluation section uses
`\label{sec:evaluation}`. LaTeX will render this as "Section ??" with an undefined
reference warning. This is an obvious error to any reviewer.

**What to do:**  
Change to `Section~\ref{sec:evaluation}`.

---

### Issue 26 — Three micro-benchmark tables share the same `\label{tab:benchmark}`

**Files:** `paper/tables/micro_100_table.tex`, `micro_1k_table.tex`, `micro_5k_table.tex`  
**Severity:** Major — produces LaTeX multiply-defined label warnings and broken `\ref{}`

**Exact duplicate label in all three files:**
```latex
\label{tab:benchmark}
```

**Why it's wrong:**  
LaTeX requires unique labels. When three tables share the same label, `\ref{tab:benchmark}`
resolves to an undefined or wrong table number, and `hyperref` may produce broken PDF
links. LaTeX emits "multiply-defined label" warnings.

**What to do:**  
Rename to `tab:benchmark-100`, `tab:benchmark-1k`, and `tab:benchmark-5k` respectively,
and update any `\ref{}` calls that point to them.

---

## Category E — Scale / Setup Mismatches

### Issue 16 — §07 experimental setup claims 100K and 1M-fact experiments

**File:** `paper/sections/07_high_arity.tex`, line 13  
**Severity:** Major

**Exact problematic text:**
```
each at scale 1K, 10K, 100K, and 1M facts
```

**Why it's wrong:**  
The `results/` directory contains only `bench_10k.*`, `quick_test.*`, and `test_run.*`.
The maximum scale benchmarked is 10K facts. Claiming 100K and 1M experiments were
conducted is factually false.

**What to do:**  
Change to "at scale 100 and 1,000 facts (matching the quick\_test suite) and 10,000 facts
(the bench\_10k suite)."

---

### Issue 17 — §08 experimental setup claims 1M-fact temporal/provenance experiments

**File:** `paper/sections/08_temporal_provenance.tex`, lines 15–16  
**Severity:** Major

**Exact problematic text:**
```
are evaluated at scale 1K--1M facts with interval widths drawn from uniform and
exponential distributions. Provenance chain depth ranges from 1 to 100 steps.
```

**Why it's wrong:**  
Same as Issue 16 — no 1M-fact results exist. The provenance chain depth claim (1–100
steps) also has no corresponding benchmark output to support it.

**What to do:**  
Replace with the actual tested scale and provenance depth range from the benchmark
configuration in `configs/benchmark.json`.

---

### Issue 15 — §limitations does not state the actual maximum tested scale

**File:** `paper/sections/limitations.tex`  
**Severity:** Moderate

**Current text:**
```
Global section computation requires $O(|\mathcal{C}| \cdot N^2)$ time in the worst case,
which limits scalability to datasets where $|\mathcal{C}|$ and $N$ are moderate
(on the order of $10^5$ facts).
```

**Why it's wrong:**  
The paper states scalability is limited to "on the order of 10^5 facts" but the actual
benchmark only ran up to 10^4 (10K) facts. This implies the system was tested at 100K,
which it was not. The number is off by one order of magnitude.

**What to do:**  
Change "$10^5$" to "$10^4$" and add an explicit sentence: "All results in this paper were
obtained at scales up to 10,000 facts. Behaviour at larger scales is extrapolated from
complexity analysis and is the subject of ongoing work."

---

## Category F — Terminology and Mathematical Accuracy

### Issue 23 — Sheaf/presheaf terminology inconsistency not addressed at point of definition

**File:** `paper/sections/formal_definitions.tex`  
**Severity:** Major for a category-theory-aware reviewer

**Why it's wrong:**  
The `conclusion.tex` and `discussion.tex` (added in the most recent commits) correctly
state that "the sheaf condition is vacuous for the Alexandrov topology on a finite poset,
where every presheaf is automatically a sheaf." However, the formal definitions section
still presents the Alexandrov topology and sheaf construction without this clarification.
A reader working through the paper in order will spend several sections believing the
system makes a non-trivial sheaf claim, only to find the retraction buried in the
conclusion. This is confusing and invites the criticism that the authors did not understand
their own formalism until the end.

**What to do:**  
Add a remark immediately after Definition 5 (Finite Topological Space) or after the
definition of the sheaf condition:
> *Remark: On a finite poset equipped with the Alexandrov topology, every presheaf
> satisfies the locality and gluing axioms automatically. The sheaf condition is
> therefore vacuously satisfied by our construction. The contribution of this paper
> is the presheaf organisation of facts over a context poset, together with the
> cross-engine verification framework and stalk-indexed query evaluation. We retain
> the "sheaf" terminology because it correctly describes the categorical structure;
> the non-trivial content lies in the construction and its performance characteristics,
> not in the satisfaction of the sheaf condition.*

---

### Issue 20 — §09 consistency figure caption makes unsupported comparative claim

**File:** `paper/sections/09_consistency_global_sections.tex`, line 28  
**Severity:** Moderate

**Exact problematic text:**
```latex
\caption{Consistency check time (C8) and global section construction time (C9) vs.\
number of overlapping contexts. SheafDB scales polynomially; constraint-based
approaches exhibit exponential growth.}
```

**Why it's wrong:**  
No comparison against a constraint-based approach was benchmarked. The "exponential
growth" of the KG/CSP baseline is a theoretical claim, not a measured one, and the
figure it captions (`global_section_scaling.pdf`) does not exist. This caption presents
an unmeasured comparative advantage as a figure result.

**What to do:**  
Remove the comparative claim from the caption. Replace with: "SheafDB consistency
check time (C8) and global section construction time (C9) vs. number of overlapping
contexts. Complexity analysis for the CSP baseline appears in
Section~\ref{sec:complexity}."

---

## Category G — Structural / Narrative Issues

### Issue 9 — Introduction §contributions list describes the old evaluation framework

**File:** `paper/sections/introduction.tex`, contributions subsection  
**Severity:** Moderate

**Why it's wrong:**  
The contributions list still says "A comprehensive benchmark evaluation comparing both
representations on identical workloads." This phrasing does not surface the paper's
strongest and most precise finding: 30× LOOKUP speedup, insert parity, 1405× GLOBAL
regression. The contribution should state the key quantitative result to anchor the
reader's expectations from page 1.

**What to do:**  
Update contribution 4 to: "A benchmark evaluation identifying a fundamental
representation tradeoff: SheafDB achieves 3–30× LOOKUP speedup via stalk-indexed
retrieval but incurs up to 1405× overhead on full-scan (GLOBAL) queries due to open-set
iteration, motivating a hybrid design."

---

### Issue 14 — C1–C10 benchmark sections are disconnected from the new evaluation framework

**Files:** `paper/sections/06_contextual_workloads.tex` through `11_mixed_flagship.tex`  
**Severity:** Moderate

**Why it's wrong:**  
The new `evaluation.tex` reports results in terms of LOOKUP vs. GLOBAL query types.
The C1–C10 sections (06–11) still describe the original per-workload taxonomy (event
reconstruction, entity neighborhood, high-arity, etc.) without connecting them to the
LOOKUP/GLOBAL split. A reader moving from §06 (workload description) to §evaluation
(results) sees two incompatible frameworks with no bridging explanation.

**What to do:**  
Add a paragraph at the end of §06 that maps C1–C10 onto the LOOKUP/GLOBAL classification:
- C1, C2, C3, C4, C7 → primarily LOOKUP workloads (stalk-indexed, SheafDB advantage)
- C5, C6 → temporal range queries (neither pure LOOKUP nor pure GLOBAL)
- C8, C9, C10 → involve GLOBAL scans (KG advantage or parity)

---

### Issue 24 — Future work does not mention the flat-fact index fix for GLOBAL queries

**File:** `paper/sections/future_work.tex`  
**Severity:** Moderate

**Why it's wrong:**  
The paper's largest measured weakness is that SheafDB GLOBAL queries are 1405× slower
than KG at 10K facts because the engine iterates over all open sets. The `discussion.tex`
correctly identifies "a production-quality implementation would add a global fact index
to bypass open set iteration for full scans" as the remedy. However, `future_work.tex`
does not include this item. Reviewers will ask "what's the path to fixing the 1405×
regression?" and expect to find the answer in future work.

**What to do:**  
Add a subsection:
> *\subsection{Global Fact Index for Full-Scan Queries}*  
> *The current implementation's GLOBAL query performance degrades to 1405× slower than
> KG at 10K facts due to open-set iteration. A flat fact index maintained in parallel
> with the sheaf structure would allow full-scan queries to bypass open-set enumeration
> entirely, matching KG performance while preserving LOOKUP advantages.*

---

### Issue 25 — Three non-functional adapters are silently present in the codebase and paper

**Files:** `src/sfdb/benchmark/engine_adapter.py`, paper system architecture section  
**Severity:** Moderate

**Why it's wrong:**  
The `engine_adapter.py` file defines `JenaEngineAdapter`, `BlazeGraphEngineAdapter`, and
`Neo4jEngineAdapter` classes. The file's own docstring says "Only KG and Sheaf adapters
have working implementations; Jena, Blazegraph, and Neo4j are stubs for future work."
However, if the paper's architecture description lists five adapters without this
qualification, a reviewer may attempt to reproduce cross-Jena results and find they don't
exist. The `final_audit.md` flagged this as "Only 2 of 5 engine adapters are functional."

**What to do:**  
(a) In `engine_adapter.py`, have the stub `__init__` methods raise `NotImplementedError`
with a message indicating they are not yet implemented.  
(b) In the paper architecture section, explicitly state: "The current evaluation uses two
engines: KnowledgeGraphEngine and SheafDatabaseEngine. Apache Jena, Blazegraph, and Neo4j
adapters are scaffolded but not yet integrated into the benchmark pipeline."

---

## Category H — Identity / Metadata (blocks public release)

### Issue 10 — artifact.tex GitHub URL points to wrong owner

**File:** `paper/sections/artifact.tex`, line with `\url{}`  
**Severity:** Moderate for public release

**Exact problematic text:**
```latex
{\small \url{https://github.com/anomalyco/semantic-fact-db}}
```

**Why it's wrong:**  
The actual repository is at `github.com/BlackSamuron0305/semantic-fact-db`. The URL in
the paper points to a non-existent GitHub account (`anomalyco`). Any reader who clicks
the link gets a 404.

**What to do:**  
Change to `https://github.com/BlackSamuron0305/semantic-fact-db`.

---

### Issue 11 — CITATION.cff contains placeholder author, ORCID, and affiliation

**File:** `CITATION.cff`  
**Severity:** Moderate for public release

**Exact problematic content:**
```yaml
authors:
  - given-names: "Author"
    family-names: "Placeholder"
    orcid: "https://orcid.org/0000-0000-0000-0000"
    affiliation: "Affiliation Placeholder"
```

**Why it's wrong:**  
`CITATION.cff` is the machine-readable citation file used by GitHub, Zenodo, and other
systems to auto-generate citations. Placeholder values mean any auto-generated citation
will be wrong. The ORCID `0000-0000-0000-0000` is not a valid ORCID.

**What to do:**  
Replace with real author name, a valid ORCID, and the real affiliation.

---

### Issue 12 — `main.tex` author field is still "Anonymous Author(s)"

**File:** `paper/main.tex`, line 54  
**Severity:** Moderate for public release

**Exact problematic text:**
```latex
\author{Anonymous Author(s)}
```

**Why it's wrong:**  
`Anonymous Author(s)` is appropriate only for double-blind peer review submissions. For
any public release, preprint, or non-blind submission, the real author name must appear.
Combined with the placeholder CITATION.cff, this makes the paper appear unfinished.

**What to do:**  
Replace with the real author name(s) and affiliation(s). If blind submission is intended,
document this separately but keep the de-anonymised version ready.

---

### Issue 13 — CITATION.cff `repository-code` URL is a placeholder

**File:** `CITATION.cff`  
**Severity:** Moderate for public release

**Exact problematic content:**
```yaml
repository-code: "https://github.com/placeholder/semantic-fact-db"
```

**Why it's wrong:**  
Same as Issue 10 — this URL is broken. GitHub and Zenodo use this field to link to the
source code. A broken URL undermines the paper's reproducibility claim.

**What to do:**  
Change to `https://github.com/BlackSamuron0305/semantic-fact-db`.

---

### Issue 30 — CITATION.cff abstract says "outperforms traditional RDF KGs" without qualification

**File:** `CITATION.cff`  
**Severity:** Minor but inconsistent

**Exact problematic content:**
```yaml
abstract: "A sheaf-theoretic approach to semantic knowledge representation that outperforms
traditional RDF knowledge graphs on contextual queries while providing native consistency
checking and global section construction."
```

**Why it's wrong:**  
The paper itself (after the recent commits) correctly states the result is a tradeoff:
SheafDB is faster on LOOKUP, slower on GLOBAL. The CITATION.cff abstract omits the
trade-off entirely, claiming unqualified outperformance. Anyone who reads the abstract
in a citation manager or on GitHub will have a misleading picture before opening the paper.

**What to do:**  
Update to: "A sheaf-theoretic approach to semantic fact storage that achieves 3–30×
LOOKUP speedup via stalk-indexed retrieval, while matching KG insert performance.
Full-scan queries are currently slower due to open-set iteration overhead, revealing
a fundamental contextual-locality vs. global-access tradeoff."

---

## Category I — Engineering / CI

### Issue 18 — LUBM generator exists but is not wired into the benchmark pipeline

**File:** `src/sfdb/datasets/lubm.py`  
**Severity:** Moderate — missed opportunity

**Why it's wrong:**  
The `lubm.py` module implements a generator for LUBM (Lehigh University Benchmark) data —
the de-facto standard for RDF store evaluation. It was added in the recent commits but
is not referenced in `scripts/run_benchmarks.py`, `configs/benchmark.json`, or the
evaluation section of the paper. LUBM is important because it would allow indirect
comparison with published results from Jena, Virtuoso, and Blazegraph. Without wiring
it into the pipeline, its existence is cosmetic.

**What to do:**  
(a) Add a LUBM benchmark configuration entry in `configs/benchmark.json`.  
(b) Import and invoke `LUBMGenerator` in `scripts/run_benchmarks.py`.  
(c) Run at least `LUBMConfig(num_universities=1)` (~600 facts) and add a LUBM row to
the evaluation section tables.  
(d) This is the only path to comparing against published Jena/Virtuoso numbers, which
is the paper's biggest credibility gap.

---

### Issue 19 — `bench_10k_summary.tex` still uses the old Q1–Q10 query structure

**File:** `results/bench_10k_summary.tex`  
**Severity:** Moderate

**Why it's wrong:**  
The summary table reports results for queries named Q1–Q10 in the old contextual workload
taxonomy. The new `evaluation.tex` reports results in terms of LOOKUP/GLOBAL query types
at three scales (100, 1K, 10K facts). The two result formats are incompatible. If any
paper section `\input`s the summary table, it will show a different query framework than
the one described in the evaluation section.

**What to do:**  
Rerun `scripts/generate_paper.py` after ensuring the benchmark runner produces results
in the LOOKUP/GLOBAL format. Alternatively, manually update the table to show the
LOOKUP/GLOBAL split matching `evaluation.tex`.

---

### Issue 27 — Test suite not re-run after 24-file code change

**Severity:** Moderate — silent regression risk

**Why it's wrong:**  
The two "updates" commits changed 24 files including `src/sfdb/kg/engine.py` (significant
refactor), `src/sfdb/sheaf/engine.py`, `src/sfdb/sheaf/presheaf.py`, `src/sfdb/optimizer/
optimizer.py`, and added 547 lines to `tests/test_cross_engine.py`. The `publication_
scorecard.md` states "321 tests passing" but that was prior to these commits. There is
no CI, so a regression could exist undetected.

**What to do:**  
Run `uv run pytest --tb=short` from the repo root and verify all tests still pass.
Record the new test count in `research/final_audit.md`.

---

### Issue 28 — No CI pipeline exists

**Severity:** Moderate for public release

**Why it's wrong:**  
There is no `.github/workflows/` directory in the repository. Every test run and
benchmark is manual. For a paper making reproducibility claims ("clean build: ✓"),
the absence of automated CI is a significant gap. Reviewers submitting an artifact
evaluation will expect to see a green CI badge.

**What to do:**  
Create `.github/workflows/ci.yml` with two jobs:
1. `test`: `uv sync --group dev && uv run pytest` on Ubuntu + Windows.
2. `benchmark`: `uv run sfdb benchmark --size small` and upload the JSON artifact.

---

### Issue 29 — Sphinx API documentation is missing

**Severity:** Minor

**Why it's wrong:**  
The `publication_scorecard.md` scores API documentation 2/5: "Source-code only; no
Sphinx/autodoc." The codebase has type annotations and docstrings throughout (e.g.,
`src/sfdb/sheaf/presheaf.py`, `src/sfdb/kg/engine.py`) but no documentation build
target. For a research artifact, auto-generated API docs lower the barrier for
other researchers to reproduce or extend the work.

**What to do:**  
Add `sphinx` and `sphinx-autodoc` to the `dev` dependency group in `pyproject.toml`.
Create `docs/conf.py` and `docs/index.rst`. Add a `docs` job to the CI workflow.

---

## Summary Table

| # | Severity | Category | File(s) |
|---|---|---|---|
| 1 | Blocking | Projected claim | `11_mixed_flagship.tex` |
| 2 | Blocking | Placeholder | `mixed_flagship_results.tex`, `11_mixed_flagship.tex` |
| 3 | Blocking | Projected claim | `07_high_arity.tex` |
| 4 | Blocking | Projected claim | `08_temporal_provenance.tex` |
| 5 | Blocking | Speculative section | `10_ablation.tex` |
| 6 | Major | Placeholder tables | `paper/tables/*.tex` (9 files) |
| 7 | Major | Missing figures | `paper/figures/` (6 missing) |
| 8 | Major | Bad cross-ref | `06_contextual_workloads.tex` |
| 9 | Moderate | Narrative | `introduction.tex` |
| 10 | Moderate | Wrong URL | `artifact.tex` |
| 11 | Moderate | Metadata | `CITATION.cff` |
| 12 | Moderate | Metadata | `main.tex` |
| 13 | Moderate | Metadata | `CITATION.cff` |
| 14 | Moderate | Structural | `06–11_*.tex` |
| 15 | Moderate | Scale mismatch | `limitations.tex` |
| 16 | Major | Scale mismatch | `07_high_arity.tex` |
| 17 | Major | Scale mismatch | `08_temporal_provenance.tex` |
| 18 | Moderate | Engineering | `lubm.py` / benchmarks |
| 19 | Moderate | Results format | `bench_10k_summary.tex` |
| 20 | Moderate | Unsupported claim | `09_consistency_global_sections.tex` |
| 21 | Blocking | Speculative section | `10_ablation.tex` |
| 22 | Blocking | Fabricated results | `10_ablation.tex` |
| 23 | Major | Terminology | `formal_definitions.tex` |
| 24 | Moderate | Missing future work | `future_work.tex` |
| 25 | Moderate | Misleading scope | `engine_adapter.py` + paper |
| 26 | Major | Duplicate labels | `micro_*.tex` (3 files) |
| 27 | Moderate | Engineering | Full test suite |
| 28 | Moderate | Engineering | Missing CI |
| 29 | Minor | Documentation | `pyproject.toml` |
| 30 | Minor | Metadata | `CITATION.cff` |
