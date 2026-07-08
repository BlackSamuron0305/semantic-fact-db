# Quality Gates

The project MUST refuse to mark itself as "research complete" if any of these conditions hold.

## Novelty Gate

- [ ] Novelty matrix has features marked as NOVEL without evidence
- [ ] Closest prior work not identified for each claimed novelty
- [ ] Literature review not conducted within last 6 months

## Claims Gate

- [ ] Any claim in paper lacks a CLAIM-NNN entry
- [ ] Any CLAIM-NNN has Evidence = MISSING
- [ ] Any CLAIM-NNN has Certainty = LOW and no mitigation plan

## Benchmarks Gate

- [ ] Claimed benchmark results not reproducible
- [ ] Seed, runs, and system info not documented
- [ ] Cross-engine verification not run for all queries
- [ ] Benchmarks only run on synthetic data (no real-world)

## References Gate

- [ ] Paper cites a reference not in bibliography.bib
- [ ] bibliography.bib has entries not cited in paper
- [ ] Closest prior work omitted from citation

## Mathematics Gate

- [ ] A theorem in the paper contradicts the implementation
- [ ] A proof has a logical gap identified during review simulation
- [ ] Mathematical notation inconsistent between paper sections

## Paper Gate

- [ ] Paper claims something that experiments contradict
- [ ] Paper omits a limitation that affects a claimed result
- [ ] Figures are placeholders (not auto-generated from real data)

## How to Use

Before marking any milestone as complete, run through this checklist. If any box is unchecked, the milestone is NOT complete.
