# `f22baf82ea81` native parametric family

This family preserves the canonical rule byte-for-byte at
`post_transform="as_is"`: crop the nonzero bounding box and swap its outer
and inner colors.  The alternative `rotate_cw` applies a clockwise rotation
after that content-dependent intermediate has been constructed.

## Why this is genuinely sequential

1. **Step A:** find the input-dependent nonzero bounding box, identify its two
   colors, crop it, and swap those colors.
2. **Step B:** choose the episode-level output orientation (`as_is` or
   `rotate_cw`) and apply it to the Step-A intermediate.

The retained counterfactual `counterfactual_crop_rotate.rkt` performs Step B
on an unswapped crop.  Its protected-Racket output differs from the selected
`rotate_cw` output, so the final answer actually depends on the Step-A value.

The generator builds the full six-demo/four-query input bank before slicing.
Inputs are therefore deterministic, prefix-stable, and identical across
settings.  The first two demonstrations distinguish all declared orientation,
crop-only, full-grid, and solid-inner-bbox rivals.  The fourth query is a
substantive 30×30 case.

The base sampler was also repaired: it now covers centered rectangles,
off-center rectangles, connected non-solid masks, and hollow rings.  This
removes the retained centered-solid-inner shortcut while preserving the exact
canonical rule.

## Reproduction

Run through the packet wrapper so the protected Racket runtime is used:

```bash
python3 review.py run python3 -m pytest -q \
  generators/f22baf82ea81/tests/test_parametric_f22baf82ea81.py
python3 review.py run python3 \
  generators/f22baf82ea81/workspace/parametric/audit.py \
  --out ../checks/f22baf82ea81/audit --seeds 32
python3 review.py run python3 -m arcpuzzles.review_base_preflight \
  f22baf82ea81 --out ../checks/f22baf82ea81/qualification
```

All evidence is authoring evidence only.  Owner acceptance and training
admission remain separate, pending actions.
