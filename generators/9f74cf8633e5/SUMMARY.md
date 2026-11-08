# 9f74cf8633e5

0-bg grid (h×w, ~7-9 by ~7-9) with 1-3 X-PATTERN motifs. Each motif: a center cell at (r, c) where the cell is 0 BUT all 4 diagonal neighbors at (r±1, c±1) are non-zero and SHARE THE SAME color. Motifs are placed with disjoint footprints (≥1-cell buffer). Rule: iterate over interior cells (r in 1..h-2, c in 1..w-2). If the cell is 0 AND all 4 diagonal neighbors are equal to the same non-zero color, fill the center with that color. Output: completed X centers.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
