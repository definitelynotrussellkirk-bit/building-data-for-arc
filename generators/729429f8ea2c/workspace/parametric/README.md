# Parametric normalized-intersection family

The default `mode=intersection` is the exact selected canonical Racket program.
The alternative first computes the normalized intersection of the unique largest
color-2 and color-3 components, then uses that input-dependent intermediate's
cell-count parity: odd intersections rotate clockwise; even intersections reflect
left-to-right. Inputs are matched across settings. The first two demonstrations
always exercise both parity branches, and the four query profiles end with a
substantive 30×30 case.

Focused check from the packet root:

```sh
python3 review.py run python3 -m pytest -q \
  generators/729429f8ea2c/tests/test_parametric_intersection.py
```

This is authoring work only; owner qualification/acceptance and training admission
remain separate.
