# Working notes: 1189131c32a4

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/1189131c32a4/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 review decision

The production generator and canonical Racket rule remain unchanged. Their pinned identities are:

- generator SHA-256: `563d9029027d65a06a2c7c01716171eb39685c7284cdb16d6024f6181cb74c8d`
- canonical program SHA-256: `cb24e365264238c0be9d5cd2e869bbb19a300270ad43bf90ddef138a66986722`
- canonical rule hash: `cb24e3652642`

The selected task supports a small, reasoning-preserving 2x2 parameter family, retained only as a task-local proposal under `workspace/parametric/`:

1. `frequency_order`: `most_outside` (canonical) or `least_outside`.
2. `tie_break`: `descending_numeric` (canonical) or `ascending_numeric`.

The default program is byte-for-byte canonical. The other three programs alter only the ranking of non-7 colors; output geometry remains one concentric ring per color. Hidden settings are fixed per episode.

## Teaching and sampling decision

The prototype reuses the selected generator's hard `tie_two_way` and `tie_three_way` profiles. Every accepted input contains both an unequal count and a numeric tie, so each demonstration separates all four declared programs. Inputs are sampled independently of the setting, demo/query prefixes are independent, all episode inputs are unique, and each query has four distinct candidate outputs. Sampling is bounded to 64 attempts per slot and fails closed on exhaustion.

This certificate is finite: it distinguishes the four declared programs only. The prototype grammar is deliberately narrower than the canonical generator and does not claim coverage of color 0, 2/3/5/6-color lessons, scattered same-color components, or the exact public inputs.

## Concrete repairs and evidence

The existing task test derived the repository root with a fixed `parents[1]` depth. The first portable staged check rejected it before pytest because that path pointed inside the task directory. The test now uses `reviewer_support.find_root(__file__)` and `canonical_path(root)`, so the same source works in the repository and copied runtime. Production generation behavior was not touched.

Retained checks:

- `checks/task-tests-before/result.json`: portable preflight failure identifying the fixed-depth path defect.
- `checks/task-tests-final/result.json`: 28 selected-task tests passed after the repair and prototype addition.
- `checks/parametric-frequency-rings/summary.json`: seed 17, all four settings, 3 demos/4 queries; 112 protected-Racket variant applications plus four canonical-pair checks; one demonstration-only survivor per episode.
- `checks/parametric-adversarial/result.json`: 65 seeds, 1,040 distinct matched inputs, 260 maximum-count episodes, forced duplicate-retry exhaustion, and 320 additional protected-Racket applications; no failure found within that bound.
- `checks/parametric-qualification/qualification.json`: native qualification passed all four settings on seeds 0 and 17 with 128 protected-Racket evaluations.
- `workspace/parametric/evidence/manifest.json`: current source/evidence inventory, SHA-256 `00f667bcff63eb035eb24a72a7b1843a131ea1bdcbceb582640d30cebc586dc8`.

## Status and next useful action

Status: **proposed and natively qualified, not accepted**. `variant_approved` and `training_admitted` remain false. The next useful action is an independent owner review of whether the two ranking axes are desirable curriculum variation, followed—only if accepted—by a fresh qualification/acceptance run and a broader sampler decision. No production, canonical, catalog, approval, or training-admission change is implied by this return.
