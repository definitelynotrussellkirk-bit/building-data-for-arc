# Working notes: 8801696784e1

## Current decision

Ready for owner source review and native qualification/acceptance. The exact canonical default remains `object_kind=symmetric`; the alternative `object_kind=asymmetric` selects a genuinely different input-dependent object before applying the bottom-right code-directed rotation and 2× enlargement. Protected Racket confirms that substituting the wrong object changes the final grid.

## Base and lesson repairs

`generator.py` remains version 3.3.0 with strict override validation, exact boundary handling, integer ARC-cell checks, deterministic generation, and no global RNG contamination. The supplied canonical rule bytes remain unchanged.

The second review removed an unintended lesson shortcut: asymmetric objects are no longer consistently below or larger than symmetric objects. Across every checked two-demo prefix, the relative vertical, horizontal, and size ordering reverses, so `object_kind` must be inferred from symmetry rather than layout or component size.

## Repeatable evidence tooling

`workspace/parametric/refresh_evidence.py` now rebuilds the complete source-bound chain in one command: task tests, native manifest, protected-Racket authoring preflight, causal witness, public projection, and first-turn privacy checks. It rejects mixed-source receipts, hashes the task tests as part of the certified source closure, publishes output by rename, and uses a durable rollback journal so a later invocation repairs an interrupted manifest/output/revision transaction after process death.

## Current verification

- 69 focused task tests pass.
- Four protected-Racket authoring-preflight jobs pass and qualify both settings.
- The source-derived witness replays selected and counterfactual programs; the wrong object changes the final output.
- Public projection covers 16 views; first-turn privacy checks pass 24 invariance mutations and four positive controls.
- `owner_accepted=false` and `training_admitted=false` remain explicit in all generated receipts.

## Limitation / next action

These are reviewer authoring receipts, not owner qualification or acceptance. The owner should inspect the returned source, replay native qualification on those exact bytes, and accept only after that fresh execution succeeds.
