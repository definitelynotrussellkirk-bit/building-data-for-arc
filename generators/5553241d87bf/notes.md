# Working notes: 5553241d87bf

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/5553241d87bf/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Review review-2546fdc25390b7a4 — native parametric family

- **Decision:** retain the approved canonical generator unchanged and add a task-local two-setting adapter. `stamp_transform=identity` returns the exact selected canonical Racket bytes; `marker_count_rotation` counts zero markers inside each target cell, reduces the count modulo four, rotates the complete asymmetric template, and then stamps it.
- **Teaching contract:** matched setting-neutral inputs; 2–6 demonstrations; 1–4 independent queries; every retained lesson exposes marker counts 1–4, literal template zero, unmarked distractors, and an asymmetric template. The fourth query is exactly 30×30 with 20 targets and nonzero content on all boundaries.
- **Sequential dependency:** target-local marker counting produces the quarter-turn intermediate consumed by template selection/stamping. The protected-Racket wrong-intermediate witness changes 66 cells when all targets are forced to one quarter turn.
- **Harness repair:** the inherited test's fixed `parents[1]/data/canonical` lookup was non-portable in staged execution. It now uses public `reviewer_support.find_root` and `canonical_pairs`; generator and canonical authority bytes were not changed.
- **Verification:** 86/86 staged task tests; 49 protected-Racket self-audit evaluations; native qualification for both settings at seeds 0 and 17; byte-identical replay; 768/768 sampler/count jobs; public projection check passed for eight one-query files.
- **Bounded peers:** `d2708f8b731b` passed its existing 35-evaluation protected-Racket audit; `c6b14e07214c` produced 90 lessons / 180 unique inputs with zero declared query-changing survivors. Neither peer source was edited or approved by this review.
- **Next owner action:** integrate the delta, replay the task-local inventory and native qualification, inspect the parameter semantics, then explicitly accept or reject the exact source closure. Nothing here admits data to training.
