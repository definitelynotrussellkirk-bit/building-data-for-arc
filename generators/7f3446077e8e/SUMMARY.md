# 7f3446077e8e

A connected color-2 object, one color-8 marker, one color-9 marker, and a
1–2-cell nuisance decoration appear on a zero background.  Translate every
color-2 cell by the directed vector from 8 to 9, paint each in-bounds target
color 3, and clip targets that leave the grid.  All original cells remain.

Version `3.0.0` exposes five exact, pixel-observable controls: `grid_h`,
`grid_w`, `shape_size`, `decoration_size`, and `copy_visibility`.  The ordinary
sampler covers all canonical dimension/palette profiles, alternates axial and
diagonal marker vectors, and alternates full/clipped copies.  Every four
consecutive examples contain two axial witnesses, so any three-example
single-query holdout refutes the canonical-fitting `diagonal_only` shortcut.

The canonical Racket program is unchanged (`RULE_HASH = 5d4c6d9ec409`).  The
selected redundant active authority text was synchronized byte-for-byte with
that canonical/raw program.

Kind: `per_puzzle`.  Imported baseline version: `2.0.2`; reviewed version:
`3.0.0`.  Approval remains a catalog/intake decision, not a generator claim.
