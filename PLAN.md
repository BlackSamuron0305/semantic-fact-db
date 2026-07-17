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

- [ ] `meet` of two incomparable sibling contexts currently returns the longer
  context instead of the longest common prefix — fix the implementation.
- [ ] `cover` check is currently a subset check, not a real topological cover —
  either implement a real cover check or rename/reframe so the paper isn't
  claiming more than the code does.
- [ ] "Stalk" is implemented as a precomputed hash index, not a direct limit —
  either build a real direct-limit stalk, or rename it to "entity index" in the
  math sections and stop using stalk/direct-limit language for it.
- [ ] Audit every "Theorem" in `theorems.tex`/`appendix.tex` — several are
  restatements of definitions. Either strengthen to an actual derived result or
  demote to "Proposition"/"Property" and drop the theorem framing. A reviewer
  who catches one padded theorem discounts all of them.
- [ ] Discuss (at minimum) whether the context poset should support DAGs, not
  just trees — real-world context hierarchies (e.g. multi-jurisdiction policy)
  aren't strictly tree-shaped. Full DAG support may be future work, but the
  paper should say so explicitly rather than silently assuming trees.

## Phase 2 — Close the GLOBAL-query gap
**Priority: P0 for a complete story, P1 minimum · Effort: ~2–3 weeks**
**This is the single highest-leverage move for Tier 2.**

- [ ] Implement the flat auxiliary index already sketched in `future_work.tex`.
- [ ] Re-run the GLOBAL workload (C9, C10) at all three scales with the fix in
  place.
- [ ] Rewrite abstract/conclusion once this lands: the story upgrades from "an
  honestly-reported tradeoff" to "a hybrid design that is fast on both LOOKUP
  and GLOBAL, with the naive version's regression documented as the reason the
  hybrid was necessary." That's a materially stronger, more memorable claim —
  and it's the most direct path from "solid" to "notable."

## Phase 3 — Statistical rigor + scale
**Priority: P0 · Effort: ~2–3 weeks**

- [ ] Wire the already-drafted methodology (outlier removal, bootstrap CIs,
  P50/P95/P99 reporting — currently sitting unused in the orphaned
  `benchmark_methodology.tex`) into the real benchmark pipeline and into
  `evaluation.tex`'s tables. Stop reporting bare means with CIs "omitted for
  readability."
- [ ] Push scale past the current 10k-fact ceiling — target 100k and, if
  tractable, 1M. LUBM starts at 100k, LDBC SF-1 at 100M; 10k reads as a toy
  scale to a systems reviewer.
- [ ] Take the LUBM wiring already landed (commit `fa42b64`) to a real scale
  (LUBM-10 or LUBM-50, not a smoke-test size).
- [ ] Add a second standard benchmark if time allows — BSBM or a WatDiv subset —
  so results aren't tied to one benchmark's query shape.

## Phase 4 — Real-system baseline
**Priority: P0 · Effort: ~1–2 months · Highest-leverage single item**

- [ ] Integrate at least one production RDF store — **Apache Jena TDB2** is the
  natural first choice: open source, SPARQL-standard, well documented, and
  already the store named in the paper's own "What This Paper Is Not" caveat.
- [ ] If time allows, a second store (Virtuoso open-source edition or
  Blazegraph) to show the result isn't specific to one implementation.
- [ ] Run the same C1–C10 workloads, plus the LUBM/BSBM runs from Phase 3,
  against the real store(s) alongside SFDB and the in-house KG baseline.
- [ ] This is what converts "faster than our own triple store" into "faster
  than a real one" — it's the one gap every simulated reviewer persona named
  first. Nothing else in this plan matters as much for credibility.

## Phase 5 — Related-work completeness
**Priority: P1 · Effort: ~1 week**

- [ ] Add a direct comparison to **RDF-star (RDF\*)**, which already targets the
  n-ary-fact motivation this paper opens with — the semantic-web reviewer
  persona flagged its absence immediately. Explain concretely why context-poset
  indexing is a different bet than RDF-star's approach, not just cite it.
- [ ] Position against labeled property graphs (Neo4j-style), which also handle
  n-ary facts natively without reification — another obvious "why not just use
  X" question to pre-empt.
- [ ] Cite incidence algebra / Möbius inversion work more concretely — the
  project's own 25-model survey (`research/future_models/`) already identified
  incidence algebras as the closest competitor; the paper should say so.

## Phase 6 — Ground it with a real-world case study
**Priority: P1/P2 · Effort: ~2–3 weeks**

- [ ] Apply SFDB to one real dataset instead of only synthetic generators — a
  biomedical drug-interaction subset or a Wikidata subset (already named as
  future work in `PROJECT_COMPLETION.md`) both fit the paper's own motivating
  examples. A concrete, resonant use case is often exactly what separates a
  solid paper from a memorable one.

## Phase 7 — Reproducibility & artifact polish
**Priority: P1 · Effort: ~1 week**

- [ ] `uv.lock` already pins the environment — add a Docker image on top for
  full reproducibility independent of host Python/OS.
- [ ] Archive code + benchmark data on Zenodo for a DOI; submit to the target
  venue's Artifact Evaluation track if one exists — artifact badges are a
  direct, low-effort lever on award consideration at most DB venues.
- [ ] Confirm a single command regenerates every figure/table in the paper from
  raw results (partially true today via `paper/figures/generated/` — verify
  end-to-end and document it in `setup.md`/README).

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

**Tier 2 (award-caliber):** Tier 1, plus Phase 2's hybrid index shipped as a
real result (not just future work), Phase 6's real-world case study, Phase 7's
full artifact, and an external review pass.

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
