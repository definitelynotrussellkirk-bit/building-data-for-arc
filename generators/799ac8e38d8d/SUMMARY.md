# 799ac8e38d8d

0-bg grid (h~8-11, w~11-13) with 3 BASE BLOBS — H_LINE_3 (1×3 horizontal), V_LINE_3 (3×1 vertical), SQUARE_2X2 — plus 0-2 random EXTRA shapes (4-cell lines, 2×3/3×2 rects, 3×3 squares) placed at non-touching positions in random non-2-3-4 colors (from {5,6,7,8,9} for bases, {1,2,3,4} for extras). Each blob is isolated (no 4-touching). Rule (ORIENTATION-BASED RECOLOR): for EACH 4-CONNECTED BLOB, COMPUTE its BBOX (bb_h × bb_w). RECOLOR every cell of the blob based on bbox shape: bb_w > bb_h → COLOR 2 (red, horizontal); bb_h > bb_w → COLOR 3 (green, vertical); bb_h == bb_w → COLOR 4 (yellow, square). Blob cell POSITIONS preserved; only colors change. Net: every blob recolored by orientation classifier (h-line→2, v-line→3, square→4).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
