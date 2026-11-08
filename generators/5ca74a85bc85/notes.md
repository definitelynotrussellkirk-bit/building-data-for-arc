# Working notes: 5ca74a85bc85

## Current repair decision

The source-bound reviews identified a teaching ambiguity in seed 0, sample indices
3, 4, 5, 6 (three demonstrations, one query). The first three pairs fit the rule
“copy the single global source bounding rectangle, filled with one source color,”
while the disconnected query requires copying only occupied cells. The retained
reproducer implements a **global** bounding rectangle. Some audit prose says
“each source object”; this repair makes no claim about that different rival.

Declare `LESSON_COMPETITORS["filled_source_bbox"]` using the first row-major
source cell's color to fill the global bounding rectangle. This gives a pure,
deterministic prediction on every declared profile, including multicolor inputs.
The shared worker now rejects automatic episodes if this rival matches every
demo but changes a query. Explicit demonstration counts preserve the episode
with `diagnostic_unsupported`, as required by the existing worker contract.
A sparse demonstration refutes the shortcut and permits the lesson.

The generated input grids, VERSION 3.0.0 keyed draws, public profiles and canonical
Racket transformation remain unchanged. The fix rejects unsupported automatic
draws; it does not add a scheduler, resample lessons, or guarantee successful
automatic generation at every seed. It checks only the declared global rival.

## Test portability

The allowed task-home test file `tests/test_generator_5ca74a85bc85.py` used a fixed
`__file__.parents` depth for canonical and base-authority data. The before stage
failed its portable-path preflight before collecting tests. Use the existing
`reviewer_support.find_root`, `canonical_path` and normalized `canonical_pairs`
helpers. No issued repository-root test mirror was edited.

## Source-bound verification

- Before: `checks/5ca74a85bc85/before-task-tests/result.json` reproduces the
  canonical path failure (task stage exit 2; outer check command exit 1).
- Red: `checks/5ca74a85bc85/red-tests.log` and `red-command.json` show four new
  regressions failing before the competitor existed, including automatic
  acceptance of the audited ambiguity.
- After: `checks/5ca74a85bc85/after-task-tests/result.json` reports 14/14 tests
  passing, including all five canonical pairs, declared profiles and new lesson
  policy/purity regressions.
- `checks/5ca74a85bc85/racket-and-adversarial.json` binds current source/rule hashes
  and confirms 16 selected-Racket labels. The audited fit vector remains
  `[true, true, true, false]`. Actual Catalog generation rejects the automatic
  audited lesson and retains explicit-count diagnostics.
- Bounded adversarial pass: multicolor left/right, boundary reflections and
  disconnected sources across all three difficulty bands (12 cases), plus all
  four held-out rotations of the audited lesson. No rival mutation, malformed
  prediction, Racket mismatch or incorrect gate result was found. The probe
  completed in approximately 12 seconds; no unrelated battery was run.

Current generator SHA-256: `8c00107d7e61cedb1139c952d86b804789650a8c7a37ea7b826ebe6ba00cbf06`.
Canonical normalized Racket hash: `f57d1e04d7d6` (unchanged).
Canonical rule text SHA-256: `d5e7b48e2e06d8d251380a140540b919bf76fb7d697caa178e76369bd93f7e37`.

The old evidence index is preserved as inherited review state; this packet does
not hand-edit audit dispositions or grant approval.
