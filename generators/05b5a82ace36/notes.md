# Working notes: 05b5a82ace36

## Current decision

Ready for owner source review and native qualification/acceptance. The exact canonical default remains `template_selector=largest`; the alternative `template_selector=smallest` selects a different input-dependent 2/4-connected template, normalizes its offsets, and stamps those offsets at colored anchors with clipping. Protected Racket confirms that substituting the wrong template changes the final grid.

## Base and lesson repairs

`generator.py` remains version 3.1.0 with strict and exact handling for `grid_h`, `grid_w`, `n_anchors`, `tpl_size`, and `texture`, integer ARC-cell validation, deterministic generation, and a visible decoy that refutes union-of-all-2/4-cells. The prior separation bug is still covered at the cell level: distant components are allowed even when one axis span overlaps.

The second review removed an unintended lesson shortcut: the largest template is no longer consistently top-left of the smallest template. Across every checked two-demo prefix, both vertical and horizontal ordering reverse, so `template_selector` must be inferred from component size rather than location.

## Repeatable evidence tooling

`workspace/parametric/refresh_evidence.py` now rebuilds the complete source-bound chain in one command: task tests, native manifest, protected-Racket authoring preflight, causal witness, public projection, and first-turn privacy checks. It rejects mixed-source receipts, hashes the task tests as part of the certified source closure, publishes output by rename, and uses a durable rollback journal so a later invocation repairs an interrupted manifest/output/revision transaction after process death.

## Current verification

- 82 focused task tests pass, including the seed-dependent separation regression.
- Four protected-Racket authoring-preflight jobs pass and qualify both settings.
- The source-derived witness replays selected and counterfactual programs; the wrong template changes the final output.
- Public projection covers 16 views; first-turn privacy checks pass 24 invariance mutations and four positive controls.
- `owner_accepted=false` and `training_admitted=false` remain explicit in all generated receipts.

## Limitation / next action

These are reviewer authoring receipts, not owner qualification or acceptance. The owner should inspect the returned source, replay native qualification on those exact bytes, and accept only after that fresh execution succeeds.
