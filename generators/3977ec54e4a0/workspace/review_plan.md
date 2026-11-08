# Chevron extension and scalar-contract implementation plan

Goal: provide a runnable, separately proposed parametric chevron family and fix the reproduced scalar-validation defect without changing valid canonical draws or the Racket authority.

Specification: WORK/DUTIES.md, WORK/PARAMETRIC-RULES.md, and the selected task's current notes.

## Decisions

- Preserve canonical marker grouping, supported depths, all four orientations, and the period-three teaching schedule.
- Prototype parameters are fill_color in {2,4,6,8} and fill_edges in {false,true}, fixed across each episode. Canonical default is (8,true). Labels come from each exact instantiated Racket program.
- Reject invalid scalar arguments at the generator boundary. Use the existing GenCtx.draw_int_strict helper for exact integer axes. None remains the existing no-override sentinel.
- Preserve VERSION 4.1.1 as the keyed RNG salt: this validation-only repair must not change valid generated grids. The final source SHA-256 identifies the new bytes.
- Keep all code changes within this task; the two random audit targets receive findings and reproducers only.

## Steps and verification

- [x] Finish the visible-only blind solve before reading source.
- [x] Start the unmodified twelve-stage baseline and retain its 132 strict-scalar findings.
- [x] Develop workspace/parametric/ first, with test_parametric_chevrons.py, exact programs, bounded rejection, public/private separation, and all-eight-setting Racket evidence.
- [x] Add tests/test_scalar_contract.py; demonstrate rejection tests fail on the issued generator. Keep six valid-output hashes as compatibility witnesses.
- [x] Modify only argument validation and strict integer draws; run the new regressions and strict defect lint.
- [x] Validate production 3-demo/4-query lessons and declared rivals using the independent workspace/canonical_episode_probe.py.
- [x] Run the strict after battery and the explicit isolated task tests; preserve failures and their actual status.
- [x] Prepare and finish the post-repair visible-only solve from the final generator bytes.
- [x] Complete both drawn audits; retain minimal source-bound reproductions.
- [x] Complete independent code review: no Critical or Important issue found; no code change requested.

Final packaging and fresh replay receipts are recorded separately in WORK/REVIEW.md, WORK/RESULTS.json and WORK/checks/handoff/. This source plan is frozen before packaging so those receipts do not change the patch being verified.

## Review focus

Invalid booleans masquerading as integers; fractional exact-axis values; invalid difficulty values; hidden parameters changing within an episode; demonstrations that fit a rival whose query output differs; leaked query labels in public challenges; loss of valid seeded reproducibility; portable imports in an isolated task runtime.

## Progress

Initial baseline is source 3f25acd65aab6959faf1754b7bcb2cd9a2ae5f455b58852a1032ade83e2e2d20. The canonical rule hash is 780d64b3096e. Prototype and canonical four-query tools are independent delegated work; this file tracks the selected-task scope.

Final source is 406ea39bd1050f238678d02ce90c50e02a8dd6e24e214d739398783ec7c5e603. After battery: 12/12 stages. Isolated task tests: 106 passed and 347 subtests passed. Prototype: all eight settings have three demonstrations and four queries, 56 unique inputs overall, 30 focused tests passed. Rotation diagnostics remain explicit limitations: 6/48 battery holdouts and 5/36 separate census holdouts are ambiguous, while both ordered-production samples pass.
