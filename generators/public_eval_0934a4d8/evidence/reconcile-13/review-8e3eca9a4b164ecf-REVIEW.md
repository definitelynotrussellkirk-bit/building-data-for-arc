# ARC Public-Evaluation Creation Review
Assignment: `review-8e3eca9a4b164ecf` from packet `c92b8ecc2cc925485ebd8692e72adf2681d1f9d920d94673f2e2ff050b6b8b48`.
Policy: `arcpuzzles-public-eval-creation-v1`; two reviewer-ready prototypes were required.
`public_eval_45a5af55`: missing family → exact concentric-square rule plus causal inside-unique-ring crop branch.
`public_eval_0934a4d8`: missing family → exact mirror/transpose-orbit reconstruction plus causal rare-marker crop branch.
Source-bound task tests: 35/35 and 44/44; fresh combined run: 79/79.
Bounded audits: 48 episodes and 288 protected-Racket evaluations per task; 7 and 9 shortcut rivals; no findings.
Broad teaching stress: seeds 0–127, 256 episodes and 1,024 public views per task; no findings.
Causal witnesses replayed through protected Racket and changed outputs (12×12→10×10; 3×4→5×4).
Saved public exports: 16 one-query views per task passed structure, identity, and privacy checks.
Final author self-review found no Critical, Important, or Minor issues; no independent subagent reviewer was available.
Limit: owner registration, unchanged native qualification, source review, and acceptance remain pending; preflight is not approval.

## What was built

### `public_eval_45a5af55`

The canonical rule removes the duplicated final row, reads the remaining monochrome row colors, and paints them as concentric two-cell-thick square layers. The alternative `inside_unique` setting first constructs the square, finds the only ring color appearing once in the retained row sequence, then crops the ring's strict interior. The task home now contains the worker generator, root and parametric Racket programs, native adapter/model, promotion/inventory metadata, notes, focused tests, and a reusable bounded audit tool.

Primary evidence: `checks/public_eval_45a5af55-tests/result.json`, `checks/public_eval_45a5af55/preflight/preflight.json`, `checks/public_eval_45a5af55/audit.json`, and `checks/public_eval_45a5af55/causal/witness.json`.

### `public_eval_0934a4d8`

The canonical rule treats color 8 as a solid rectangular occluder and reconstructs every hidden cell from the square's horizontal, vertical, and transpose orbit. The alternative `marker_bbox` setting recovers the hidden patch, selects its unique least-frequent color, and crops the bounding box spanning the two hidden marker cells. The sampler uses bounded three-color orbit assignments so first-color and most-frequent-color bounding boxes do not alias the intended marker crop.

Primary evidence: `checks/public_eval_0934a4d8-tests-retry/result.json`, `checks/public_eval_0934a4d8/preflight/preflight.json`, `checks/public_eval_0934a4d8/audit.json`, and `checks/public_eval_0934a4d8/causal/witness.json`.

## Verification and review

The retained source-bound receipts cover original labels, generated Python/Racket parity, worker controls, malformed-input rejection, 2–6 demonstrations, one to four queries, shuffled prefix-stable query order, setting blindness, public first-turn projection, size stress through 30×30, rival rejection, protected-Racket syntax, preflight, and causal replay. `checks/final-self-review.json` verifies immutable parent hashes, literal `RULE_TASK_ID` declarations, root/canonical Racket equality, current source bindings, evidence statuses, non-inert counterfactuals, and the 128-seed teaching stress.

The initial disposable task-test run for `public_eval_0934a4d8` timed out at 240 seconds even though the identical pytest flags completed in-place in about 20 seconds. A fresh isolated source-bound retry with a 600-second allowance passed 44/44, and the final combined suite passed 79/79 in 26.16 seconds. Both receipts and this limitation are retained.

## Owner boundary

Both outcomes are reported as `prototype` with parametric status `ready`. They are not catalog-approved, owner-qualified, accepted, or training-admitted. The owner must preserve accepted source during reconciliation, register the `ee_<parent>` authority, rerun unchanged native qualification and acceptance, and resolve any overlapping public-parent return before admission.
