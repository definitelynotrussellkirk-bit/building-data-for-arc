# `8e7f766c96bf` frame-dimension family

This task-local native prototype preserves the canonical `fixed_4x4` setting byte-for-byte and adds `anchor_dimensions`. In the alternative setting, the first hollow blue frame in row-major order supplies an input-dependent `(height, width)` intermediate; every frame with those dimensions then receives a red interior.

The six demonstrations and four independently revealable queries use identical inputs across settings. The first two demonstrations vary the anchor dimensions and include repeated anchors, 4x4 frames, same-height/same-width distractors, more-frequent distractor dimensions, and strict smaller/larger frames. The bounded audit checks all-frame, anchor-only, second-frame, smallest/largest, one-axis, most-frequent, fixed-3x3, and fixed-5x5 rivals. Query four is a substantive 30x30 boundary case.

Run from the packet root:

```sh
python3 review.py run python3 -m pytest -q \
  generators/8e7f766c96bf/tests/test_parametric_anchor_dimensions.py
python3 review.py run python3 \
  generators/8e7f766c96bf/workspace/parametric/audit.py \
  --out generators/8e7f766c96bf/workspace/parametric/evidence/current
python3 review.py run python3 -m arcpuzzles parametric qualify 8e7f766c96bf \
  --out ../checks/8e7f766c96bf/qualification --summary
```

These are reviewer artifacts only. Qualification does not perform owner acceptance or training admission.
