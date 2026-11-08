# 02b21c59893a generator repair design

## Outcome

Teach the selected canonical rule directly: exactly one blue source anchor, the last red anchor in row-major order as destination, payload colours preserved under translation, and off-board translated cells clipped. Remove the undocumented no-blue fallback and rule-hiding empty-payload modes from the production domain.

## Distribution

Use a deterministic five-role cycle so every five consecutive labeled pairs contains all roles and every four-demo query rotation keeps at least one counterexample to each declared rival:

1. `canonical_anchor`: 8x9, palette 6, one red, no clipping.
2. `offset_anchor`: 9x10, palette 7, one red, no clipping.
3. `last_red`: 7x11, palette 5, two reds, no clipping.
4. `last_red_clip`: 9x11, palette 7, two reds, partial clipping.
5. `clip_multicolor`: difficulty-scaled noncanonical canvas, one red, partial clipping.

The first four roles exactly match the four canonical `(height, width, palette-size)` profiles. Every role places blue away from both `(0,0)` and the payload bounding-box origin. Two roles contain multiple red anchors and two contain partial clipping.

## Public contract

Expose one exact observable axis, `scene_profile`. Reject unknown keys, wrong types, unknown profile names, and unsupported difficulty values. `observe_overrides` recovers the profile from pixels. Pin `RULE_HASH = "ba8a3944ecbc"`, set `EXAMPLES_NEEDED = 4`, and declare full strict support.

## Semantic evidence

Declare independent executable rivals for source-at-origin, source-at-payload-bbox, first-red destination, and all-or-nothing clipping. Link each to a witness and score all four in `lesson_identifiable`. A task-local independent probe reproduces the canonical rule, materializes Racket parity, and exhaustively checks cyclic starts/query rotations.

## Validation

Task-local tests are written before the generator rewrite. They cover canonical acceptance/parity, exact override round-trips, seed-861 regression, five-role cyclic identifiability, malformed inputs, deterministic replay, profile support, diversity, and live Racket parity. Final validation uses task tests, required-rotation semantic gate, complete battery, and 100 lessons per band with query rotation.
