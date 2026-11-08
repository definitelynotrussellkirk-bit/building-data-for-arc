# 87aae821984d

Version `4.0.0` generates a zero-background grid containing one logical cyan motif and one to five isolated yellow counter cells. The cyan motif may be disconnected and has a tight bbox of 2×2, 2×3, 3×2, or 3×3.

Rule: count yellow cells; right/bottom-align every cyan cell in a fixed 3×3 tile, padding short/narrow motifs on the top/left; repeat the tile horizontally once per yellow cell. Output shape is always `3 × (3N)`.

The four-period teaching schedule covers full-span, top-padded, left-padded, top-and-left-padded, connected, and fragmented motifs. The exact override surface is `grid_h`, `grid_w`, `n_4_cells`, and `shape_kind`; all joint combinations are constructive and observable.

Selected Racket authority: `RULE_HASH = 6f52927247b0`. Final generator SHA-256: `15a3c012540738dee4d3d31f9ffe68b8eebfcdfda23836b0cc4c3be0fd9b99b8`.
