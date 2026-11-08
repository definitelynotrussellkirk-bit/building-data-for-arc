# f151fbd31cb2

A 0-background grid contains one singleton shape key, one singleton color key,
and one or two disconnected green objects from each of two families. Shape key
1 selects L-triominoes; shape key 4 selects plus-pentominoes. Color key 2, 6, or
8 supplies the replacement color. The output recolors every object in the
selected family and preserves all other cells.

Generator version `3.0.0` exposes six exact observable axes: `grid_h`, `grid_w`,
`shape_key`, `color_key`, `n_l`, and `n_plus`. A three-slot curriculum cycles
through selected-majority, selected-minority, and balanced family counts so the
canonical majority/area shortcuts are not lesson-identifiable.

Kind: `per_puzzle`. Rule pin: `33294c3c6e8b`.
Approval is derived by the catalog from current code and retained evidence.
