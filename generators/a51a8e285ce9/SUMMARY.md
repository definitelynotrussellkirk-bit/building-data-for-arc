# a51a8e285ce9 — Match a prototype family up to symmetry

Three equal-width panels are separated by full-height color-8 columns. The first
two panels contain connected prototype polyominoes; the third contains a
rotation or reflection of exactly one prototype in a different color. Return the
**displayed orientation** of the matching prototype, tightly cropped and
recolored with the query color.

## Selected generator

- Version: `4.0.0`
- Canonical rule hash: `d76e03446f2a`
- Lesson size: 4 demonstrations
- Geometry: height and panel width each 4–7; total width `3*panel_w+2`
- Prototype area: 5–8 cells
- Transform family: all eight D4 rotations/reflections
- Palette size: 4 or 5, including lawful examples where a prototype itself is
  color 8; separator parsing is therefore geometric, not color-component based.

Generated prototype pairs have equal area, distinct free-polyomino classes, and
full eight-element D4 orbits. Equal area removes the cell-count shortcut that
fits the canonical pairs. The deterministic four-example teaching schedule
covers both match roles, a reflection-only case, orientation normalization, and
recoloring. Objects receive independent legal offsets inside their panels.

Exact overrides are supported for `grid_h`, `panel_w`, `prototype_size`,
`match_index`, `transform`, and `palette_size`; unknown, mistyped, and out-of-
range values are rejected. `observe_overrides`, structural/strict validators,
semantic rivals and witnesses, malformed mutation fixtures, and an independent
workspace oracle support source-bound auditing.

Kind: `per_puzzle`. Approval remains catalog-derived; this review does not alter
the selected Racket authority.
