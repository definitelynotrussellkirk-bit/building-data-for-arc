# Working notes: 46b45dd2aff8

## 2026-10-24 — query-rotation-safe lesson schedule

- **Defect confirmed:** the prior `horizontal, color_trap, vertical, color_trap` schedule was identifiable only in production order. Holding out the sole trap in a three-pair window left two demonstrations compatible with the color-blind nearest-aligned-rectangle shortcut; the strict semantic gate found 6 ambiguous rotations out of 36.
- **Decision:** use the explicit period-8 schedule `H,C,C,C,V,C,C,C` and declare `LESSON_SCHEDULE_PERIOD = 8`. Every length-three window contains at least two actual color traps, so any one-pair query holdout leaves a decisive trap demonstration.
- **Constraint preserved:** slots 0 and 4 remain the non-trap horizontal/vertical profiles. This keeps the existing slot-0 exact canonical-profile defaults; a naïve trap at slot 0 would degrade to a one-color horizontal scene on easy samples.
- **Regression:** the task test now checks easy/medium/hard windows starting at indices 0–15, verifies at least two color-identity witnesses, and holds out each of the three pairs in turn.
- **Evidence:** focused tests pass 7/7; semantic gate reports 0/36 ambiguous sampled rotations and the complete declared-period census reports 0/72 ambiguous rotations across 24 lessons; Racket mirror parity is 120/120.
- **Rule authority:** unchanged (`RULE_HASH = 95e121aa05f4`); this repair changes only generator scheduling, tests, and notes.
- **Next useful action:** maintainer replay/acceptance. This review does not itself approve the generator or admit it to training.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7441e7a9c8f26ad9:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `9d4ea374ff445b7c1f25d67e38744258a1ddd400a56e0a36083f8b0688aeca67`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source 96adb179aa9ece68ec9e3af2d274a8e12aa18e9dd4a980f59f1b7c5c983d20a5 declares period8 H,C,C,C,V,C,C,C. Reviewer reports7focused tests, 0/36sampled and0/72enumerated ambiguous rotations, with120Racket parity cases. This explicitly repairs the reported rotated-holdout gap; finite scope remains in current task notes. No owner rerun claimed.

### Assessment or prior finding

## 46b45dd2aff8

### A3 — Reproduced teaching defect under permitted query rotation

Source binding: generator SHA-256 `9d4ea374ff445b7c1f25d67e38744258a1ddd400a56e0a36083f8b0688aeca67`; authority source SHA-256 `c661b1608bae808155516d9cfa4876feda32c797e88028e1bd285b817fb595cf`; declared rule hash `95e121aa05f4`.

The generator is otherwise well specified: its isolated audit and seven task tests pass, and all 60 sampled production-order lessons refute the declared competitors. The defect is in the claimed rotation support. Its schedule is `H,C,V,C,...`, where `C` is the only color-trap profile. For an `H,C,V` bundle, rotating `C` into the query leaves `H,V` as demonstrations. The declared `nearest_aligned_ignoring_color` rival fits both demonstrations but predicts a different query output.

A source-bound census of 20 lessons per band materialized 60/60 lessons and 180 labeled pairs (178 unique inputs). Production order had 0/60 ambiguous lessons. Holding out every pair once produced 180 rotations, of which **30 were ambiguous** and 30 raised the matching lesson hook warning—10 in each band. There were no materialization or scoring errors.

The exact first witness is seed `55441714`, requested sample index `0`, easy band. Original pair indices `0` (`horizontal`) and `2` (`vertical`) are demonstrations; original pair index `1` (`color_trap`) is the query. The authority and rival differ at 12 cells. Full grids, outputs, hashes, and replay command are retained in `checks/audit/46b45dd2aff8/rotation-counterexample.json`; independent authority replay is `checks/audit/46b45dd2aff8/racket.json`.

**Evidence:**

- `checks/audit/46b45dd2aff8/lesson-census.summary.json`
- `checks/audit/46b45dd2aff8/rotation-counterexample.json`
- `checks/audit/46b45dd2aff8/racket.json`
- `checks/audit/46b45dd2aff8-combined/result.json` (seven tests and ordered semantic gate pass)

**Suggested repair:** if arbitrary query rotation is intended, place at least two color traps in every three consecutive materialized pairs (for example a `C,C,H,C,C,V` period) and add a test that holds out each pair. Otherwise declare an ordered-only lesson policy and run rotations diagnostically rather than as supported behavior.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7441e7a9c8f26ad9-v0001/audit_assets.json), manifest SHA-256 `a6922d5379fd772e8669459f295fbdd1dcd7ebda127a119d912d35412292c82f`.
<!-- arcpuzzles-current-audit-assessment:end -->
