# 04204350555e

0-bg grid (h ∈ 5-7, w ∈ 7-9) with: N ∈ 1-2 ISOLATED NON-BG SEED CELLS, each in a color drawn at random from {2..9}, placed at random positions with MANHATTAN-DISTANCE >4 between any pair (so their radius-2 diamonds don't overlap). Rule (FOR EACH NON-BG SEED CELL AT (R0, C0) WITH COLOR k, PAINT EVERY CELL (R, C) WITHIN MANHATTAN DISTANCE 2 WITH COLOR k — A 13-CELL DIAMOND): For EACH non-bg cell at (r0, c0) with color k: For EVERY (r, c) WHERE |r-r0| + |c-c0| ≤ 2 (in-bounds): PAINT g[r][c] = k. The seed cell itself stays k; the 4 cells at distance 1 (cardinal neighbors) get k; the 8 cells at distance 2 (longer diagonals + outer cardinals) get k. Out-of-bounds cells drop. Net: each seed becomes a 13-cell colored diamond (rhombus); the rest of the grid stays 0.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
