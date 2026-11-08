# 51860663947e

0-bg grid (h~8-16, w~11-19) with: (a) 1-2 (default) VERTICAL FULL-HEIGHT WALLS at columns chosen by one of 5 POSITION BIASES (spread / centered / left_heavy / right_heavy / diagonal), all painted COLOR 2; (b) 1-2 HORIZONTAL WALLS that span only ONE SECTION (between two vertical walls or between a wall and the grid edge), creating DISTINCT 0-REGION SIZES; (c) optional DISTRACTOR cells of color 2 (≤5% density). The 2-walls split the bg-0 cells into ≥3 disjoint 4-CONNECTED REGIONS of distinct sizes (MAX and MIN are unique). Rule (RECOLOR THE MAX-SIZE 0-REGION TO 1 AND THE MIN-SIZE 0-REGION TO 8): extract every 4-CONNECTED region of bg-0 cells (blocked by color-2 walls). RANK regions by cell count. SELECT the LARGEST region — PAINT every cell with COLOR 1 (blue). SELECT the SMALLEST region — PAINT every cell with COLOR 8 (cyan). Other regions stay bg-0. The 2-walls stay color 2. Net: the largest open chamber turns blue; the smallest turns cyan; middle-sized regions stay black.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
