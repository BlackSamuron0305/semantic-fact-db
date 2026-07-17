# Draft / superseded sections

These `.tex` files are **not** `\input` by `paper/main.tex` and do not appear in
the compiled PDF. They were moved here from `paper/sections/` on 2026-07-17
during a repo-hygiene pass (see `PLAN.md`, Phase 0) because they were sitting
alongside the live sections and could be mistaken for current content.

Known issues with specific files, for context if one is ever revived:

- `sheaf_model.tex` states the sheaf condition without the vacuity caveat that
  the compiled paper (`sections/mathematical_model.tex`,
  `sections/introduction.tex`) relies on — reconcile that before reusing it.
- `system_design.tex` describes a third engine ("SimplicialDB") that does not
  exist in the current architecture (`sections/system_architecture.tex`
  describes only the KG and Sheaf engines) — this was an earlier three-engine
  design that was abandoned.
- `benchmark_methodology.tex` describes a more rigorous statistical protocol
  (Grubbs-test outlier removal, bootstrap confidence intervals, P50/P95/P99
  reporting) than what `sections/evaluation.tex` currently reports. It was
  never wired into the actual benchmark pipeline. See `PLAN.md` Phase 3 —
  if that work lands, this file is the starting point.
- `results.tex`, `datasets.tex`, `experimental_setup.tex`, `architecture.tex`,
  `kg_architecture.tex`, `kg_storage.tex`, `kg_query_engine.tex`,
  `sheaf_storage.tex`, `restriction_maps.tex`, `global_sections.tex`,
  `query_execution.tex` are earlier drafts superseded by the versions of this
  material folded into the currently-`\input`'d sections
  (`evaluation.tex`, `system_architecture.tex`, `implementation.tex`,
  `mathematical_model.tex`, `correctness.tex`).

If reviving any of these, check them against the current compiled paper for
consistency first — several were written before the paper's honesty pass
(commit `456514c` and later) and may overclaim relative to current house style
(see the DevVault project note `standards.md` → "Don't oversell the math").
