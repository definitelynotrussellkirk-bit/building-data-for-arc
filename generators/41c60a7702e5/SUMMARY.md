# 41c60a7702e5

0-bg grid (h~8-10, w~11-14) with 2 SOLID RECTANGLES at hardcoded positions: (a) a 2×7 RECTANGLE at (1, 1)..(2, 7) in one non-zero color; (b) a 4×4 RECTANGLE at (4, 4)..(7, 7) in another color. NOTE: currently both fixed sizes — diversity is intrinsic-low (only color permutations). Rule: for EACH BLOB (connected component), COMPUTE: (1) boundary cell count (cells with ≥1 bg/non-blob neighbor); (2) total size; (3) color. SORT blobs by (BOUNDARY DESC, SIZE DESC, COLOR DESC). SELECT the FIRST blob (max boundary). Output: an EMPTY GRID of the same dimensions with ONLY that selected blob, RECOLORED to COLOR 8 (cyan). All other blobs and bg are cleared. Net: input has multiple rectangles; output preserves only the one with most boundary cells, painted cyan.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
