# cd4b705f95d4

0-bg grid (h~7-9, w~9-11). ROW 0 contains k=2..3 color-1 (blue) cells at random distinct columns (the COUNT/target-size). BODY (rows 1..h-1) contains EXACTLY 2 color-3 (green) BLOBS of DISTINCT sizes (one with 2 cells, one with 3 cells), positioned at fixed slots (rows 2, cols 1 and 6). EXACTLY ONE color-2 (red) ANCHOR cell at fixed (5, 5) with room for the translated blob. Rule: count color-1 cells in row 0 → k. Find the green BLOB whose cell count equals k. TRANSLATE that blob so its bbox top-left lies at the red anchor's position. PAINT the translated cells with color 8 (cyan) on the existing grid. Original green blobs, the red anchor, and row-0 count stay. Net: the count selects the matching blob; output adds a cyan copy at the anchor.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
