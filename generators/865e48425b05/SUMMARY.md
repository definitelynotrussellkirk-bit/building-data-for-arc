# 865e48425b05 — Palette Mask Multiplication

Read the sparse nonzero palette in row 0 from left to right. Crop the connected color-1 mask below the empty separator row to its tight bounding box. Emit one recolored mask copy per palette entry, preserving holes and palette order, with exactly one zero column between adjacent copies.

The v2.0.1 generator exposes four exact observable axes (`grid_h`, `grid_w`, `n_palette`, `mask_id`), retains all five canonical size/palette profiles, covers 2–4 palette colors and 12 connected mask shapes, and uses a four-sample teaching cycle. Any four consecutive examples include two non-3x3 masks and two unsorted palettes, so holding out any one query still refutes the canonical-fitting fixed-3x3 shortcut and the numeric-sort shortcut. Declared rivals also cover no-gap concatenation and solid-bounding-box fill.

Kind: `per_puzzle`. Reviewed version: `2.0.1`. Canonical `RULE_HASH`: `efb1009fca26`.
Approval remains derived by the catalog from current code and retained evidence.
