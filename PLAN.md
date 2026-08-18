# SFDB — Path to Publication-Ready / Award-Caliber

Written 2026-07-17, based on a full read of the compiled paper plus the project's
own self-critique docs (`research/reviewer_simulation.md`, `research/risk_register.md`,
`research/final_audit.md`). Those docs already did the hard, honest work of naming
the gaps — this plan turns that list into a sequenced, actionable roadmap.

## Starting point, stated plainly

The paper's core strength is that it's honest: it discloses the vacuous sheaf
condition, reports a 1405× GLOBAL-query regression prominently, and explicitly
scopes out what it doesn't claim. That discipline is worth protecting through
everything below — every phase should *tighten* the honesty, never trade it away
for a flashier number.

The paper's core weakness, confirmed independently by all four personas in the
team's own `reviewer_simulation.md`: **every comparison is SFDB vs. an in-house
research-prototype triple store.** There is no result anywhere against a real RDF
system. That is the single fact most likely to sink a submission, ranked by the
simulated reviewers above the toy 10k-fact scale and above the vacuous-sheaf
framing (which is already defused by being upfront about it).

## Two-tier goal

- **Tier 1 — Publication-ready**: defensible at a solid DB-systems or KR venue;
  survives a real reviewer asking "compared to what?" and "at what scale?"
- **Tier 2 — Award-caliber**: Tier 1, plus a genuine hero result (not just an
  honestly-reported tradeoff) and a case a committee remembers.

---

## Phase 0 — Repo & paper hygiene
**Priority: P0 · Effort: ~1 day · Blocking: nothing, do this first**

- [x] Move or delete the orphaned `paper/sections/*.tex` files never `\input`
  by `main.tex`. Done 2026-07-17: 14 files moved to `paper/drafts/`
  (`architecture.tex`, `benchmark_methodology.tex`, `datasets.tex`,
  `experimental_setup.tex`, `global_sections.tex`, `kg_architecture.tex`,
  `kg_query_engine.tex`, `kg_storage.tex`, `query_execution.tex`,
  `restriction_maps.tex`, `results.tex`, `sheaf_model.tex`,
  `sheaf_storage.tex`, `system_design.tex` — includes the dead "SimplicialDB"
  third-engine draft in `system_design.tex`, and `sheaf_model.tex`, which
  states the sheaf condition without the vacuity caveat the compiled paper
  relies on). Note: `formal_definitions.tex`, `theorems.tex`, and
  `mathematical_foundations.tex` looked orphaned by filename but are actually
  live — nested via `\input` inside `mathematical_model.tex` and
  `background.tex` respectively; left in place. See `paper/drafts/README.md`
  for per-file notes.
- [x] Resolve the test-count discrepancy. Done 2026-07-17: ran
  `uv run pytest --collect-only -q` → **347 tests collected**, matching the
  paper's figure. README's "321" was stale; updated to 347 in both places it
  appeared.
- [x] `benchmark_methodology.tex` moved to `paper/drafts/` (see above) rather
  than deleted, since Phase 3 may want to promote it to real — it's the
  starting point for that work, flagged as such in `paper/drafts/README.md`.
- [x] Added pre-honesty-pass snapshot notices to `research/final_audit.md`,
  `research/publication_scorecard.md`, and `research/PROJECT_COMPLETION.md`
  (the last wasn't in the original list but has the same issue) pointing to
  this plan and noting they predate the LOOKUP/GLOBAL hedge in the current
  abstract.

## Phase 1 — Fix math/implementation precision gaps
**Priority: P0 · Effort: ~1 week**

The theory-reviewer persona in `reviewer_simulation.md` found spots where the
category-theory vocabulary overclaims what the code actually does. Fix the code
to match the math, or the words to match the code — pick one per item, don't
leave the mismatch:

- [x] `meet` fixed 2026-08-16: it was returning the longest common prefix
  unconditionally, which is the *join*, not the meet — a real mathematical
  error (the paper's own open-set-intersection theorem was false for
  incomparable contexts as a result). Meets are now correctly partial:
  `None` for incomparable contexts, matching the corrected theorem. Fixed
  in both `common/types.py` and `sheaf/sheaf.py`, pinned by
  `tests/common/test_context_lattice.py`.
- [x] `cover`/`is_cover` fixed 2026-08-16: was a bare subset check with a
  docstring admitting it "simplifies." Now checks that the family covers
  every stored context strictly below the target, matching the stated
  Alexandrov-topology semantics.
- [x] Stalk-as-hash-index reconciled 2026-08-16 (words-to-code direction):
  added a derivation to `formal_definitions.tex` showing the direct limit
  *collapses* to `F(minimal neighbourhood)` on an Alexandrov space, which
  is exactly what the hash index materialises — not a rename, a proof that
  the existing name is earned.
- [x] Theorem audit: done in the pre-2026-08-16 restructuring — non-load-bearing
  theorems moved to the appendix with an explicit "not cited by number
  elsewhere, recorded as a completeness check, not a load-bearing result"
  framing (`appendix.tex`). The one theorem the paper's argument actually
  depends on (cross-engine equivalence) stays in place in `correctness.tex`.
- [x] DAG discussion added 2026-08-16 to `limitations.tex` §"Mathematical
  Assumptions": states the tree assumption explicitly, names a concrete
  DAG use case, and explains what a DAG extension would cost (invalidates
  the prefix-string encoding and the $O(d)$ insert path).

## Phase 2 — Close the GLOBAL-query gap
**Priority: P0 for a complete story, P1 minimum · Effort: ~2–3 weeks**
**This is the single highest-leverage move for Tier 2.**
**Status: done (pre-2026-08-16 session).**

- [x] Flat stalk index implemented; GLOBAL now resolves through it instead of
  open-set enumeration.
- [x] Re-run at all scales with the fix in place — GLOBAL is now
  37×–102× faster than KG (not a regression), confirmed again in the
  2026-08-16 re-run including the new $10^5$-fact scale.
- [x] Abstract/conclusion rewritten accordingly.

## Phase 3 — Statistical rigor + scale
**Priority: P0 · Effort: ~2–3 weeks**
**Status: mostly done.**

- [x] 95% confidence interval half-widths now reported alongside every mean
  in `query_latency.tex`/`insert_latency.tex` (2026-08-16), generated by
  `scripts/generate_tables.py` from `compute_statistics`'s existing
  bootstrap/normal-approximation output — no longer "omitted for
  readability."
- [x] Scale pushed to $10^5$ facts (2026-08-16) — this is what surfaced the
  restriction-graph $O(n^2)$ bug (see `discussion.tex`'s bug inventory),
  confirming the plan's own prediction that a fixed scale ceiling can hide
  problems.
- [ ] $10^6$ facts — not attempted.
- [ ] LUBM at real scale (LUBM-10/50) — loader exists (`sfdb.datasets.lubm`),
  still not wired into the benchmark runner.
- [ ] BSBM/WatDiv — both now cited with verified bibliography entries
  (`related_work.tex`), neither has been run as an actual workload against
  any engine.

## Phase 4 — Real-system baseline
**Priority: P0 · Effort: ~1–2 months · Highest-leverage single item**
**Status: done, 2026-08-16.**

- [x] Integrate at least one production RDF store — done: a real Apache Jena
  TDB2 6.2.0 instance, run via its Fuseki HTTP server against a disk-backed
  TDB2 dataset, accessed only over the standard SPARQL 1.1 protocol
  (`JenaTDB2EngineAdapter` in `src/sfdb/benchmark/engine_adapter.py`,
  `scripts/jena_reference.py`). Not a stub, not rdflib — a genuine external
  Java process this project's authors did not write.
- [x] Run all five query classes (not the old C1–C10 taxonomy, which
  predates the current benchmark suite — see `paper/sections/evaluation.tex`)
  at all four paper scales (100–100,000 facts) against Jena, alongside SFDB,
  with result counts verified identical on every row.
- [x] Result (corrected 2026-08-17, see the CONTEXT-bug item below): a
  genuine crossover, not a clean win, but narrower than first measured.
  SFDB is faster than Jena
  on LOOKUP, GLOBAL, and CONTEXT at every scale ($2.44\times$,
  $8.8\times$, and $2.00\times$ respectively at $10^5$ facts, despite
  Jena paying HTTP
  overhead SFDB does not). Jena overtakes SFDB on TEMPORAL from
  $10^4$ facts onward, roughly $6.7\times$ faster at $10^5$ facts — a
  mature
  production optimiser beating SFDB's Python-level candidate filtering once
  candidate sets reach tens of thousands of rows. See
  `paper/sections/evaluation.tex` §"External Reference Point: Apache Jena
  TDB2" for the full writeup. An earlier version of this run reported
  Jena also overtaking SFDB on CONTEXT and attributed a large CONTEXT
  measurement-variance finding to process-level effects; both are
  retracted — see the CONTEXT-bug item below.
- [x] A second store — done: OpenLink Virtuoso (open-source edition,
  v7.20.3243), run via Docker, accessed over HTTP Digest-authenticated
  SPARQL 1.1 (`VirtuosoEngineAdapter`, `scripts/virtuoso_reference.py`),
  reproducing the identical methodology at all four paper scales. Result:
  the same pattern, independently — SFDB faster on LOOKUP/GLOBAL/CONTEXT at every
  scale ($3.3\times$, $15\times$, $3.7\times$ at $10^5$ facts), Virtuoso faster on
  TEMPORAL from $10^4$ facts onward (roughly $7.1\times$ at
  $10^5$ facts) — against a second, independently engineered optimiser from
  a different organisation. This answers the question this item's Jena
  writeup left open: the pattern is not Jena-specific. See
  `paper/sections/evaluation.tex` §"External Reference Point: OpenLink
  Virtuoso". Building this comparison also surfaced a genuine cross-engine
  SPARQL semantics divergence (Virtuoso does not filter untyped-literal
  relational comparisons the way Jena/rdflib do), fixed once in the shared
  query text used by all three external comparisons and now pinned by a
  regression test (`tests/benchmark/test_virtuoso_adapter.py`).
- [x] GraphDB, as a third store — done: Ontotext GraphDB (free edition,
  v10.7.3), run via Docker with no auth and no named-graph requirement
  (`GraphDBEngineAdapter` auto-creates its repository via GraphDB's REST
  API on first use, `scripts/graphdb_reference.py`), reproducing the
  identical methodology at all four paper scales. Result: the same
  pattern a third time, independently — SFDB faster on LOOKUP/GLOBAL/CONTEXT at
  every scale ($1.80\times$, $6.3\times$, $1.63\times$ at $10^5$ facts), GraphDB faster
  on TEMPORAL from $10^4$ facts onward (roughly $6.3\times$ at
  $10^5$ facts) — against a third, independently engineered optimiser
  from a third organisation. Unlike Virtuoso, GraphDB's plain-literal
  relational comparisons already behave correctly (no STR() workaround
  needed, though the shared query text uses it uniformly regardless), so
  this comparison surfaced no new query-portability bug — but it was the
  trigger, alongside LUBM below, for re-verifying CONTEXT everywhere. See
  `paper/sections/evaluation.tex` §"External Reference Point: Ontotext
  GraphDB".
- [x] LUBM standard-benchmark-workload run against the three in-house
  engines — done: `sfdb.datasets.lubm.LUBMGenerator`, extended with a
  one-semester temporal envelope on `takesCourse`/`teacherOf` facts
  (it previously had none), run at four university-count scales
  (`scripts/lubm_benchmark.py`) landing close to this paper's usual four
  fact-count scales.
- [x] LUBM run against all three external stores as well, varying both axes
  (dataset and comparison engine) at once — done 2026-08-17:
  `scripts/lubm_external_reference.py --store {jena,virtuoso,graphdb}`,
  identical LUBM data/queries/anchors as the in-house LUBM run above,
  against real Jena/Virtuoso/GraphDB instances over the same HTTP/SPARQL
  path used elsewhere. Result: the pattern holds exactly, against every
  store, at every scale, every result count matching — SFDB faster on
  LOOKUP/GLOBAL/CONTEXT (e.g. Virtuoso at 97,289 facts: $1801\times$,
  $13\times$, $262\times$), the external store faster on TEMPORAL from
  $10^4$ facts onward. This is the strongest robustness check in the
  paper for the central crossover claim, since no other comparison varies
  both the dataset and the engine at once. See
  `paper/sections/evaluation.tex` §"LUBM Against External Stores: Varying
  Both Axes at Once". Not yet run at the much larger scales published
  LUBM results use — still open.
- [x] **A major correction, found via the LUBM run above.** LUBM's
  topology (many large, mutually unrelated top-level contexts — one per
  university) exposed a genuine performance bug in SFDB's own CONTEXT
  query resolution
  (`src/sfdb/sheaf/optimizer.py::_classify_semilocal`), present for the
  *entire* evaluation and invisible to every prior comparison: CONTEXT
  resolution fanned out through every ancestor open set a matching fact
  belonged to, including the open set for `context:world` (which every
  fact in the corpus belongs to whenever the query context is not the
  root), instead of the direct $O(1)$ lookup on `context:<c>` the
  architecture already materialises at insert time and that
  `paper/sections/complexity.tex` already assumed was what happened.
  Final results were always correct (a downstream filter narrows the
  over-broad candidate set back down), which is why cross-engine
  verification never caught it and why the balanced synthetic generator
  never exposed it (it grows a query's own target subtree in lockstep
  with total corpus size, so wasted and legitimate work scale together).
  Measured effect: a CONTEXT query anchored on a fixed 68-fact department
  went from $0.68$ms to $350$ms ($515\times$) as unrelated universities
  were added elsewhere. Fixed by targeting `context:<c>` directly;
  pinned by `tests/sheaf/test_context_query_scope.py` (confirmed to fail
  against the pre-fix code). Because CONTEXT appears in every comparison
  this paper reports, fixing it required re-running and re-verifying
  **every benchmark**: `sfdb benchmark` (main paper suite),
  `scripts/rdflib_reference.py`, `scripts/jena_reference.py`,
  `scripts/virtuoso_reference.py`, `scripts/graphdb_reference.py`,
  `scripts/wikidata_case_study_benchmark.py`, and
  `scripts/lubm_benchmark.py` itself — all re-run and re-verified
  2026-08-17. Two earlier claims are retracted as a direct consequence:
  the paper's own CONTEXT-measurement-variance finding (which was
  measuring this bug, not process-level noise), and the Wikidata case
  study's CONTEXT-loses-to-KG-mem finding (also this bug). The corrected
  picture is a *stronger* result: SFDB now shows a robust advantage on
  three of five query classes (LOOKUP, GLOBAL, CONTEXT) rather than two,
  against every baseline and every external store, and the crossover
  this paper is built around narrows to TEMPORAL alone.
- [ ] The BSBM/WatDiv standard-workload runs are still not done. LUBM against
  a real store is now done (see above), at all four scales, against all
  three stores.
- This converted "faster than our own triple store" into "faster on the
  query shapes the design targets, slower on the ones it doesn't, against a
  real one" — a more credible and more informative result than either a
  clean win or the untested gap this plan named as the biggest risk. Then
  the second store converted a single-vendor result into a
  cross-optimiser one, the third turned "cross-optimiser" into a
  pattern robust enough to call a property of mature production engines
  generally, the LUBM run turned "two query classes cross over" into
  "one does" by finding and fixing a real bug the first three comparisons
  had all been silently affected by, and running LUBM against all three
  external stores confirmed the corrected pattern survives varying the
  dataset and the engine simultaneously, not just one axis at a time.

## Phase 5 — Related-work completeness
**Priority: P1 · Effort: ~1 week**
**Status: done, 2026-08-17.**

- [x] Add a direct comparison to **RDF-star (RDF\*)**, which already targets the
  n-ary-fact motivation this paper opens with — the semantic-web reviewer
  persona flagged its absence immediately. Explain concretely why context-poset
  indexing is a different bet than RDF-star's approach, not just cite it. Done:
  `paper/sections/related_work.tex` §"Statement-level annotation and
  $n$-ary mitigation" — RDF-star and singleton-property encoding both
  covered, with the concrete architectural distinction (annotate
  statements vs. index by context; a fact is still $k$ triples plus
  quoted-triple annotations vs. one atomic storage unit) rather than a
  bare citation.
- [x] Position against labeled property graphs (Neo4j-style), which also handle
  n-ary facts natively without reification — another obvious "why not just use
  X" question to pre-empt. Done: `paper/sections/related_work.tex`
  §"Labeled property graphs" (new, 2026-08-17) — concrete architectural
  contrast (LPGs dissolve reification for binary facts with metadata but
  not for arity $\geq 3$; no native context-poset equivalent; scoping
  falls back to per-query property filters or per-tenant databases), an
  honest statement that no LPG store is benchmarked directly and why
  (the KG baseline's reified-triple design is architecturally closer to
  the RDF stores actually compared against), and a pointer to a fourth-store
  LPG comparison as a named future-work extension
  (`paper/sections/future_work.tex` §"Integration With Production RDF Stores").
- [x] Cite incidence algebra / Möbius inversion work more concretely — the
  project's own 25-model survey (`research/future_models/`) already identified
  incidence algebras as the closest competitor; the paper should say so. Done:
  `paper/sections/related_work.tex` §"Categorical and topological database
  models" states it concretely and cross-references
  `paper/sections/future_work.tex` §"An Incidence-Algebra Query Layer".

## Phase 6 — Ground it with a real-world case study
**Priority: P1/P2 · Effort: ~2–3 weeks**
**Status: done, 2026-08-16.**

- [x] Apply SFDB to one real dataset instead of only synthetic generators — a
  biomedical drug-interaction subset or a Wikidata subset (already named as
  future work in `PROJECT_COMPLETION.md`) both fit the paper's own motivating
  examples. A concrete, resonant use case is often exactly what separates a
  solid paper from a memorable one. Done: a genuine Wikidata dataset — 5,337
  national head-of-state/head-of-government "position held" facts (198
  positions, 168 countries, P580/P582 start/end dates on 92.6%/89.0% of
  facts), fetched from Wikidata's public SPARQL endpoint and cached
  (`data/wikidata_case_study_raw.json`, `scripts/fetch_wikidata_case_study.py`,
  `sfdb.datasets.wikidata_case_study`) so the benchmark never depends on
  Wikidata's live data. Ran the identical five-class benchmark
  (`scripts/wikidata_case_study_benchmark.py`) against KG/KG-mem/SFDB with
  full three-way cross-engine verification (every class agreed on every
  engine). The result is **not** a clean confirmation, which is itself the
  valuable part: LOOKUP, GLOBAL, and CONTEXT reproduce the synthetic-benchmark
  advantage cleanly, but TEMPORAL *reverses* relative to
  its synthetic-benchmark storage-layer-control result — TEMPORAL beats KG-mem on real data where it did not
  survive the KG-mem control on synthetic data. Direct, if narrow (one
  domain, one scale), evidence that one of the paper's four reported
  margins is sensitive to a dataset's actual shape, not only to scale —
  see `paper/sections/evaluation.tex` §"Real-World Case Study: Wikidata
  Office-Holders" for the full writeup, including two data-sourcing dead
  ends (a 504 timeout from an unfiltered label query, severe sample skew
  from an unrandomised join) documented in
  `scripts/fetch_wikidata_case_study.py`'s module docstring. (An earlier
  run of this comparison reported CONTEXT also reversing,
  losing to KG-mem; that reading was a symptom of the CONTEXT bug fixed
  under Phase 4 and is retracted along with every other CONTEXT number
  this bug touched.)

## Phase 7 — Reproducibility & artifact polish
**Priority: P1 · Effort: ~1 week**
**Status: two of three items done, 2026-08-16.**

- [x] `uv.lock` already pins the environment — add a Docker image on top for
  full reproducibility independent of host Python/OS. Done: `Dockerfile` at
  the repo root, built and run end-to-end (`docker build -t sfdb .`,
  `docker run --rm sfdb`) — 402 tests pass, the 14 tests requiring a live
  Jena/Virtuoso/GraphDB instance correctly skip inside the isolated container, and
  `docker run --rm sfdb uv run sfdb benchmark` was smoke-tested too. Does
  not include TeX Live (PDF build) or the external Jena/Virtuoso/GraphDB stores,
  which is documented in the README and the image's own header comment
  rather than left implicit.
- [ ] Archive code + benchmark data on Zenodo for a DOI; submit to the target
  venue's Artifact Evaluation track if one exists — artifact badges are a
  direct, low-effort lever on award consideration at most DB venues. Not
  attempted: this requires an actual account, a real upload, and a minted
  DOI — a public, effectively irreversible action outside what an
  autonomous session should do without the user directly driving it.
- [x] Confirm a single command regenerates every figure/table in the paper from
  raw results — verified end-to-end 2026-08-16: `uv run python
  scripts/generate_tables.py` and `uv run python scripts/generate_figures.py`
  both regenerate cleanly from `results/*.json` alone, and
  `paper/sections/artifact.tex` documents the full command sequence
  (`uv sync` through `latexmk -pdf main.tex`) including the two external-store
  scripts as a clearly separated addendum.

## Phase 8 — Writing & venue strategy
**Priority: P1 · Ongoing**

- [ ] Given the contribution profile (systems-flavored, honest negative
  results, a hybrid fix), target a DB-systems venue with an experiments/applied
  track (SIGMOD/VLDB applications track) or KR, rather than a pure-theory venue
  — the project's own reviewer simulation already concluded LICS/CSL is the
  wrong fit.
- [ ] Get 1–2 external (non-author) reads before submission. The self-review
  docs are unusually good, but an outside reader catches framing problems the
  team can no longer see.
- [ ] Once Phases 2 and 4 land, rewrite the abstract's headline claim: from "a
  documented tradeoff" to "faster on the queries that matter, at parity on
  insert cost, validated against a real RDF store, with the one gap we found
  closed by a hybrid index."

---

## Definition of done

**Tier 1 (publication-ready):** Phases 0–3 complete, plus Phase 4 with at least
one real-system comparison landed.
**Status as of 2026-08-17: essentially met, and exceeded.** Phases 0–2 done;
Phase 3 done
except $10^6$-scale and BSBM/WatDiv-as-a-workload; Phase 4's core
criterion (one real-system comparison landed) is done and a second and
third store
(Virtuoso, GraphDB) have since independently reproduced the same finding, plus
a LUBM standard-workload run against the in-house engines *and* against all
three external stores simultaneously — three real
production stores and a standard benchmark workload, all five query classes, all four scales, verified
result counts throughout, with the dataset and the engine varied together as
the final robustness check. Building the LUBM comparison also found and
fixed a real performance bug (Phase 4's CONTEXT-bug item) that had been
affecting every CONTEXT number in the paper; the corrected result is a
narrower, cleaner crossover (SFDB wins three of five query classes
against every store, not two) than first reported, and that corrected
pattern reproduces again against every store on the LUBM-vs-external-store
run. Phase 5 (related-work completeness) is now done, including the
labeled-property-graph positioning added 2026-08-17. What's left for a
clean Tier 1 close-out is only the external review pass Phase 8 calls
for, which nothing in a solo session can substitute for.

**Tier 2 (award-caliber):** Tier 1, plus Phase 2's hybrid index shipped as a
real result (not just future work), Phase 6's real-world case study, Phase 7's
full artifact, and an external review pass.
**Status as of 2026-08-17:** Phase 2's result shipped (see above). Phase 6
(real-world case study) is done — a genuine Wikidata dataset, benchmarked
with full cross-engine verification, that surfaced a real and unflattering
nuance (TEMPORAL reverses direction on real data)
rather than a tidy confirmation, and a genuine LUBM standard-workload run
that additionally caught and fixed a real bug, subsequently reproduced
again against all three external stores with the dataset and engine
varied simultaneously. Phase 7 is two-thirds done (Docker image
built and run end-to-end; single-command regeneration verified); only Zenodo
archival and AE-track submission remain, and those need the user's own
account and a public, effectively irreversible action, not something a
solo session should do autonomously. The remaining gap to Tier 2 is
narrower than it was: Phase 8's external review pass, which nothing in a
solo session can substitute for, and the Zenodo/AE-track step above.
Whether the crossover finding (SFDB wins on LOOKUP/GLOBAL/CONTEXT, real production
optimisers win on TEMPORAL at scale, reproduced independently
against three unrelated engines, then complicated further by two
real/standard datasets that agree on three classes and diverge on the
fourth) is itself enough
of a "case a committee remembers" is a judgement call for an external
reader, not something this document can determine on its own — though a
paper that found and fixed a bug of this magnitude in its own central
result, and reported the fix and the retraction plainly rather than
quietly moving the numbers, is a stronger case for that judgement than
the paper was a day earlier.

## Suggested sequencing

Phase 0 first (cheap, immediate). Phases 1–3 can run loosely in parallel since
they touch different code. Phase 4 (real baseline) is the long pole — start it
early even though it won't finish first. Phase 2 (hybrid index) is the best
return on effort for moving from "solid" to "notable," so don't let it slip to
the end. Phases 5–8 layer on top once the core evidence (2–4) is in.

Rough total effort: ~3–4 months focused solo work to Tier 1; ~5–6 months to
Tier 2, dominated by Phase 4's integration work and Phase 6's case study.

## Explicit scope traps — do not chase these for this paper

- **Cohomological consistency checking / incidence-algebra hybrid** (both named
  as future work in `PROJECT_COMPLETION.md`) — genuinely interesting, but they
  are a *follow-up paper's* contribution, not a requirement for this one.
  Pursuing them now is the most likely way to blow the timeline without
  addressing anything a reviewer actually flagged.
- **Persistence / transactions / concurrency** — the systems-reviewer persona
  named this, but it's orthogonal to the sheaf-vs-triple argument. Keep it
  explicitly scoped out in `limitations.tex`, as it already is, rather than
  building it.
