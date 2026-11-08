# Native parametric family: 4ebdc8d865ce

`selection=isolated_twos` is the exact canonical program: recolor only
four-connected singleton color-2 components to 1.

`selection=anchor_sized_twos` first finds the unique color-3 component and binds
its occupied-cell area. It then recolors every color-2 component having exactly
that area to 1. Thus step A (anchor discovery and measurement) supplies an
input-dependent size needed by step B (component selection and recoloring).

Inputs are matched across settings. The first two demonstrations vary the anchor
area and contain singleton, equal-area, near-area, large, same-area color-4, and
diagonally touching distractors. Four query roles cover transfer, larger geometry,
a substantive 30×30 boundary scene, and a wide scene. `public_turn()` exposes all
demonstrations and exactly one query input, keeping settings, programs, labels,
and future queries private.

## Reproduce

From the packet's outer directory:

```sh
python3 review.py run python3 -m pytest -q \
  generators/4ebdc8d865ce/tests/test_parametric_4ebdc8d865ce.py
python3 review.py run python3 \
  generators/4ebdc8d865ce/workspace/parametric/audit.py \
  --out ../checks/4ebdc8d865ce/final/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify \
  4ebdc8d865ce --out ../checks/4ebdc8d865ce/qualification --summary
```

The first command checks the adapter contract and generated lessons, the second
runs the finite demonstration-only rival audit, and the third executes the native
source-bound qualification through protected Racket. These commands prepare a
reviewer handoff only; they do not perform owner acceptance or training admission.
