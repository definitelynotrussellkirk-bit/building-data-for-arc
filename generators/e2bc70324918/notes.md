# Working notes: e2bc70324918

## Current decision

Keep generator `3.2.0` and promote the two-setting `stamp_mode` family (`copy`, `dilate4`). `copy` is byte-identical to the canonical Racket program. `dilate4` forms a genuine A → intermediate → B rule: extract the observed source glyph, compute its orthogonal dilation, then stamp that exact cell set at the original line endpoints.

## Repairs and reversals

The imported generator ignored or under-supported several declared controls, lacked the canonical X/I stencil coverage, and checked only line endpoints rather than the full endpoint stamp footprint. Those defects are covered by regressions and repaired in `generator.py`. The `no_line` diagnostic path also had an indexing crash; its reproducer now passes.

An initial filled-bounding-box variant was rejected during adversarial review because a bounding-box/fixed-motif shortcut could replace the intended intermediate. It was replaced with input-shape-dependent orthogonal dilation. The minimum two-demo lesson holds the source bounding box at 3×3 while varying both the source template and its dilated intermediate.

## Current evidence

- `checks/e2bc70324918-tests-final/result.json`: 10 task-local tests passed.
- `workspace/parametric/evidence/self-audit.json`: 92 protected-Racket evaluations; 46/46 setting pairs distinguish.
- `checks/e2bc70324918/adversarial-self-review.json`: 256 seeded episodes, 1,536 setting comparisons, and 28 unseen-seed protected-Racket evaluations passed.
- `checks/e2bc70324918/qualification/qualification.json`: authoring preflight passed with 28 parametric labels, eight original canonical pairs, and 40 protected-Racket evaluations.
- `checks/e2bc70324918/causal/witness.json`: canonical undilated substitution changes the final protected-Racket output.
- `checks/e2bc70324918/first-turn.json`: four first turns, 24 private-field invariance checks, and four visible-change controls passed.

## Next owner action

Review the exact integrated source, rerun native qualification and acceptance on that binding, and separately decide training admission. No owner acceptance is claimed here.
