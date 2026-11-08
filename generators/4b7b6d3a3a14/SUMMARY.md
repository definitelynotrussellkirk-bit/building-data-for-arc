# 4b7b6d3a3a14

0-bg grid (h ∈ 6-8, w ∈ 7-9) with: (a) ONE CORNER MARKER at FIXED position (0, 0) — value ∈ {1, 2} (1 = horizontal mirror to right; 2 = vertical mirror to bottom); (b) ONE CONNECTED MOTIF in a non-{0, 1, 2} color drawn from {3,4,5,6,7,8,9} — 3-5 cells built by _build_motif random walk, placed in the UPPER-LEFT QUADRANT (rows 1..h//2-1, cols 1..w//2-1) with no overlap. Rule (READ THE (0,0) MARKER, MIRROR THE MOTIF TO THE OPPOSITE HALF; ORIGINAL MOTIF PRESERVED): READ the (0, 0) marker value. IF MARKER = 1 (HORIZONTAL): for EACH motif cell at (r, c) PAINT g[r][w-1-c] with the same color (mirror LEFT→RIGHT across the central column). IF MARKER = 2 (VERTICAL): PAINT g[h-1-r][c] (mirror TOP→BOTTOM across the central row). Original motif cells and (0, 0) marker stay untouched. Net: a corner code drives either an LR or UD reflection of the motif into the opposite half of the grid.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
