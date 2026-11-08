# Review notes: `ca81880afbf3`

## Base repair

The supplied ordinary generator had concrete retained defects: advertised layout
controls were inert, scalar overrides were silently coerced or clipped, declared
width metadata disagreed with generated draws, and self-check admitted trivial
impostors. `generator.py` is now version 2.0.0 and:

- strictly validates seeds, indices, difficulty, names, scalar types, and ranges;
- realizes exact square/rectangle counts and dimensions or rejects an impossible
  request rather than clipping or dropping shapes;
- implements four distinct layout biases (`scattered`, `row_aligned`,
  `col_aligned`, `diagonal`) with isolated frame construction;
- exposes `observe_overrides(grid)` for every exact numeric control;
- keeps authoring-only degenerates outside the ordinary valid domain; and
- preserves every canonical input accepted by the source task.

Native lint, self-check, and rule-smoke pass. Defect lint reports zero in-scope
issues. Its sole remaining warning is a pre-existing behavior-equivalent text
mismatch between archival selected `target_code` and active canonical authority;
that file lies outside the two assigned generator homes and was not edited.

## Parametric family

- `finish_rule=fill_only` is the exact canonical/default Racket program.
- `finish_rule=bridge_equal_area` first fills complete square holes with color 2,
  then connects horizontally or vertically aligned equal-area derived color-2
  components through their centers with color 4.
- Inputs are matched across settings; streams are independent and prefix-stable.
  Counts are 2–6 demonstrations and 1–4 queries. The fourth query is a substantive
  30×30 scene with five square components, two relay pairs, an unequal square,
  a rectangular negative, and distractors.
- The protected shifted-center witness preserves every fill but corrupts the
  intermediate centers consumed by the bridge stage; the final output changes
  by 20 cells.

## Retained verification

- 55/55 staged task tests (48 base-repair cases plus 7 family cases).
- 16-seed family audit: 32 episodes, 320 pairs, 640 demonstration-prefix checks,
  320 query-prefix checks, 320 setting-output changes, 320 shifted-center
  ablation changes, and 32 30×30 queries.
- Authoring preflight: four source-bound jobs and 32 protected-Racket labels.
- Public projection: 16 independent one-query views; 24 private-field invariance
  checks and four positive controls.

## Handoff limits

The repaired base and family are reviewer-ready, not owner-accepted. The owner
must review the exact source, run native qualification, reconcile any desired
archival rule-text beautification separately, and freshly accept the integrated
bytes. Finite checks do not prove universal lesson uniqueness.
