# fdffdd0bbde7

A 3–6-row top library contains 2–4 panels separated by full-library-height
color-9 columns. Each panel has one visible color-9 anchor and 1–5 cells of one
unique non-9 color. A blank row separates the library from 4–8 lower body seeds.
For each body seed, stamp the matching panel's colored offsets relative to its
visible anchor onto a blank output, clipping at the grid boundary.

The six exact controls are `grid_h` (10–16), `grid_w` (13–21), `lib_h` (3–6),
`n_entries` (2–4), `stencil_size` (1–5), and `n_body` (4–8). Production anchors
vary off center in both coordinates; declared rivals test assumptions that the
anchor is at the panel center, center row, or center column.

Kind: `per_puzzle`. Imported version: `4.0.0`.
Approval is derived by the catalog from current code and retained evidence.
