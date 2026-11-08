# Enclosed-region review implementation plan

**Goal:** Return a runnable rule-parameter prototype, concrete canonical-generator repairs, honest visible-only solves, and a replayable delta package.

**Architecture:** Keep the canonical Racket transformation fixed. Put the parameterized rule and episode authoring tool in `workspace/parametric/`; keep production semantic contracts in `generator.py`; use portable reviewer helpers in task tests.

**Tech stack:** Python 3.12+, pytest, NumPy/Pillow supplied by the check environment, bundled Racket 8.10.

**Requirements:** `WORK/DUTIES.md`, `WORK/PARAMETRIC-RULES.md`, and `WORK/RETURN-GUIDE.md` from the unchanged assignment review-ed01d6ce549e92d3. Only selected task files and assigned selected authority copies are editable.

## Independent deliverables

- [x] Complete the untouched blind solve before opening any task implementation.
- [x] Develop the task-local area-threshold prototype first; test canonical default, fixed episode parameters, Racket parity, competing thresholds and public/private separation. Final prototype v1.1.0 balances threshold and connectivity witnesses.
- [x] Reproduce scalar-input rejection failures, then reject invalid seed/index/difficulty and Boolean grid colors before generation. Keep lawful calls deterministic; treat `scene_profile=None` exactly like an omitted override.
- [x] Replace the editable test file's fixed ancestor/private-loader assumption with `reviewer_support` and preserve its semantic assertions.
- [x] Apply reviewed whitespace-only synchronization to the two selected `target_code` copies; preserve canonical program and archival source.
- [x] Reproduce the canonical-fitting rectangle shortcut, add two bounded stepped-room profiles and executable rival/witness/lesson checks, and retain source-bound final counterexample evidence.
- [x] Verify final implementation and prototype locally: 55 main tests / 159 subtests, 27 prototype tests, nine balanced Racket-labelled episodes, 36 query rotations, and 30 profile/parameter controls. Retain honest intermediate failures and higher-threshold eight-neighbor survivors.
- [x] Run strict after battery, portable task tests, and the required lesson census; preserve baseline and intermediate failures.
- [x] Perform exposed visible-only solve from final source, draw and complete two findings-only audits, then write reports and command receipts.
- Final handoff after source freeze: package, replay the exact delta from the original archive in a fresh runtime-closure extraction, run focused tests there, compare changed-file hashes, and return the builder-produced ZIP. Completion and receipts are recorded in top-level REVIEW.md and RESULTS.json; this source plan is not changed after replay.

## Review focus

Invalid scalar arguments must fail before expensive work. Canonical and all advertised scene profiles must remain lawful and observably controllable. A generated witness must really disagree with the intended Racket label. Demonstration sufficiency and held-out rotations need distinct counts. Prototype parameters must never leak into public files or change within an episode. Finite rival checks do not prove universal identifiability.
