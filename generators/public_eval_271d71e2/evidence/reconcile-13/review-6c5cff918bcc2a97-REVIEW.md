# Review handoff — review-6c5cff918bcc2a97
Status: both assigned public-family prototypes are reviewer-ready; all owner gates remain pending.
Tasks: `public_eval_b99e7126` and `public_eval_271d71e2`.
Source: new task-local generators, general Racket references, parametric adapters, tests, audits, and inspection tools.
`b99e7126` defect → repair: missing family → source-faithful tile-blueprint completion with identity/clockwise poses.
`271d71e2` defect → repair: missing family → capped frame motion plus state-coupled clockwise/counterclockwise fill sweeps.
Focused checks: 44 tests passed, including all eight supplied labeled pairs through protected Racket.
Bounded checks: 64 episodes, 640 pair instances, 512 executable-rival checks, and 48 protected-Racket audit evaluations.
Public boundary: 256 one-query exports written and 256 deliberate visible-cell modifications rejected.
Causality: both source-bound counterfactual witnesses replayed through protected Racket.
Limits: authoring preflight is not owner qualification or acceptance; no training data was admitted.

## `public_eval_b99e7126`

The canonical rule treats the novel-color cells inside the unique anomalous tile as a blueprint over the tile lattice. Existing anomalous tiles determine the blueprint's unique macro placement, and the output completes every missing target with the same anomalous motif. The canonical `identity` setting matches the immutable public parent; `rotate_cw` poses the blueprint before placement while keeping matched inputs.

The family supports 2–6 demonstrations and four distinct private queries. Its constructive bank includes irregular masks, placement ambiguity guards, two-demo rival rejection, and lawful 29×29 stress. The retained executable rivals cover no completion and bounding-box completion. An early cross-runtime discrepancy exposed a Python bounding-box oracle bug: it used lexicographic point extrema instead of independent row/column extrema. The corrected oracle now agrees with its Racket counterpart.

Final evidence:

- 22 focused tests passed.
- 16-seed audit: 640 requests, 32 episodes, 320 pair instances, 160 distinct inputs, 256 Python rival checks, 24 protected-Racket evaluations, 128 public files, and 128 tamper rejections.
- 84 stress examples reached 29×29.
- The source-bound preflight passed and all four supplied labeled pairs matched.
- The counterfactual replaces the rotated intermediate with the identity pose and changes the final output.

Future-agent tools are task-local: `inspect_blueprint.py` exposes the inferred normal/anomalous motifs, blueprint, pose, placement, and targets; `audit.py` performs the repeatable semantic/rival/public-boundary sweep.

## `public_eval_271d71e2`

The canonical rule finds the black framed panel, its attached red bar, and the same-span target bar. It computes `actual_travel = min(target_distance, remaining_gray_cells)`, translates the frame and attached bar by that amount, and converts exactly that many gray cells to orange in a direction-dependent clockwise edge sweep. The alternate setting reverses the transverse sweep order while preserving matched inputs.

The family supports 2–6 demonstrations and four distinct private queries. Its bank includes all four motion directions, capped and uncapped cases, multiple frame geometries, and 30×30 stress. The retained executable rivals omit filling or use the full target distance. Construction is cached and bounded, with a deterministic fallback scene to prevent pathological retry loops.

Final evidence:

- 22 focused tests passed.
- 16-seed audit: 640 requests, 32 episodes, 320 pair instances, 153 cross-bank distinct inputs, 256 Python rival checks, 24 protected-Racket evaluations, 128 public files, and 128 tamper rejections.
- 350 labeled examples exercised capped travel; 48 reached 30×30.
- The source-bound preflight passed and all four supplied labeled pairs matched.
- The counterfactual substitutes full target distance while preserving the counterclockwise sweep and changes the final output.

Future-agent tools are task-local: `inspect_motion.py` reports frame/target geometry, gray count, target distance, actual travel, translation, and both sweep orders; `audit.py` performs the repeatable semantic/rival/public-boundary sweep.

## Owner handoff

For each task, register the literal `RULE_TASK_ID`, review the exact task-local source, refresh the native inventory, run unchanged native qualification, and perform fresh acceptance. Preserve the canonical defaults and reconcile any overlapping public-parent contribution rather than silently overwriting accepted source.
