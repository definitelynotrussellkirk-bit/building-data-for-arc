# d2f386d0e071 — Complete the Vertical Mirror

A zero-background grid contains 4–9 sparse colored source cells on or left of
the vertical midline. Widths may be even (the axis lies between columns) or
odd (a center-column source is legal and mirrors to itself). Every off-axis
mirror destination starts blank.

The selected rule is `(overlay g (flip-lr g))`: preserve each source and copy
its color to `(row, width - 1 - column)`. The generator schedules even-width,
odd-width, and centerline examples so a lesson refutes identity, pure-flip,
up/down reflection, nearest-axis-only, one-color-only, off-by-one-axis, and
centerline-duplication shortcuts.

Exact override axes:

- `grid_h`: 5..12
- `grid_w`: 7..14
- `n_cells`: 4..9
- `n_distinct_colors`: 2..4

Kind: `per_puzzle`. Reviewed generator version: `3.0.0`. Canonical rule hash:
`f48a460c6519`.
