# 7514c6f65f15

0-bg grid (h×w, ~8-11 by ~9-12) containing exactly 3 connected blobs in 3 distinct non-zero colors (≠ 8). Blobs have 3, 4, and 5 cells. Their BBOX HEIGHTS are strictly distinct (so the tallest is unambiguous). Blobs don't 4-touch (≥1-cell buffer). Rule: sort all components by bbox-height descending (then by size desc, then top-left row asc, then col asc). Pick the top one. Recolor all its cells from its original color to 8. Other blobs preserved. Output: same grid with the tallest blob's cells now color 8.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
