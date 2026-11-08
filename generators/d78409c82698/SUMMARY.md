# d78409c82698

0-bg grid (h~8-13, w~8-13) with: (a) 2-5 COLOR-2 (red) SINGLETON CELLS placed at positions with no cardinal red neighbor (diagonal-neighbor pairs are allowed and used to pin CARDINAL, not diagonal, connectivity); (b) ONE FIXED MULTI-CELL COLOR-2 CLUSTER at bottom-left (a 3-cell L-shape at (h-3, 0), (h-2, 0), (h-2, 1)) — a non-singleton red blob that should NOT be recolored. Rule: for EVERY COLOR-2 (red) CELL, check its 4 cardinal neighbors. If ALL 4 cardinal neighbors are NON-RED (any non-2 value), RECOLOR that cell to COLOR 3 (green). If ≥1 cardinal neighbor IS red (part of a multi-cell component), KEEP it as 2. Net: cardinally isolated red singletons become green; multi-cell red blobs stay red.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
