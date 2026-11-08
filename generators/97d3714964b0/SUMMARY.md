# 97d3714964b0

A zero-background grid, 7–14 rows by 9–14 columns, contains one or two
hollow color-7 rectangular frames and one or two solid color-7 rectangles.
Objects occupy four separated slots, and at least one hollow/solid pair has
identical bounding-box dimensions. The input palette is exactly `{0, 7}`.

For each 4-connected color-7 component, inspect the strict interior of its
bounding box. If any interior position is background 0, recolor the component
yellow (4); otherwise recolor the solid component red (2). Other cells are
preserved.

The four exact controls are `grid_h`, `grid_w`, `n_hollow`, and `n_solid`.
The generator pins canonical rule hash `3c6d01646411`, accepts all canonical
inputs, and declares three canonical-fitting size rivals that every generated
scene refutes through a same-bbox hollow/solid witness.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
