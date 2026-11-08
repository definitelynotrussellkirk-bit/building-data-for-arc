# 3cf7be88b563

0-bg grid (h~6-8, w~8-10) with: (a) 1-2 ISOLATED COLOR-1 (blue) CELLS at INTERIOR positions (rows 1..h-2, cols 1..w-2); (b) 1-2 ISOLATED COLOR-2 (red) CELLS at INTERIOR positions. Cells are placed via a chosen POSITION BIAS (scattered, spread, centered, corners) with min Manhattan separation ≥3 between any pair (so each marker is isolated). Rule (EXPAND COLOR-1 BY CARDINAL ADJACENCY, COLOR-2 BY DIAGONAL ADJACENCY): For EACH 0-CELL at (r, c): (i) if any of its 4 CARDINAL NEIGHBORS (up/down/left/right) is COLOR 1, PAINT (r, c) to COLOR 1. (ii) ELSE if any of its 4 DIAGONAL NEIGHBORS (nw/ne/sw/se) is COLOR 2, PAINT (r, c) to COLOR 2. Cells already non-0 stay. Net: each 1-marker grows a plus halo, each 2-marker grows an X halo (when cardinal vs diagonal criteria differ).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
