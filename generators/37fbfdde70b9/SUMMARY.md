# 37fbfdde70b9

0-bg grid (h ∈ 6-9, w ∈ 7-10) with: SEED_COUNT ∈ 2-4 SINGLE COLORED CELLS, each in a DISTINCT non-bg color drawn from {1..9}, placed at random positions where: (a) row ∈ 0..h-2 (not the bottom row, so a downward ray has room to extend); (b) col ∈ 1..w-1 (not col 0, so a leftward ray has room); (c) each seed sits on a DISTINCT anti-diagonal (r + c differs across seeds) so rays don't overlap. Rule (FROM EACH SEED, DRAW A DOWN-LEFT (↙) DIAGONAL RAY OF THE SAME COLOR ALL THE WAY TO THE GRID BORDER): For EACH seed at (r, c) with color k: PAINT cells (r+i, c-i) for i = 1, 2, ... until either r+i ≥ h OR c-i < 0 (out of bounds). Each ray cell painted color k. Seeds stay at their original positions. Net: each seed shoots a downward-leftward diagonal of its color to the grid edge.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
