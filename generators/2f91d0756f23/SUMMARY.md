# 2f91d0756f23

0-bg grid (h~6-9, w~7-10) with: (a) ROW-0 COUNT MARKERS — k COLOR-1 (blue) cells at random columns of row 0 with k ∈ {1, 2, 3, 4}; (b) COLOR-9 (maroon) ANCHOR at interior (anchor_r, anchor_c) with anchor_r ∈ [2, h-3], anchor_c ∈ [2, w-3]; (c) 1-3 ORBIT CELLS in non-{0, 1, 9} colors at positions within ±2 of the anchor (adjacent or near, not overlapping). Rule (ROTATE EACH ORBIT CELL AROUND ANCHOR k TIMES BY 90° CCW): READ k = COUNT of color-1 cells in row 0. PRODUCE a fresh output grid with anchor at (anchor_r, anchor_c) painted 9. For EACH ORBIT CELL at (r, c) with color C and offset (dr, dc) = (r - anchor_r, c - anchor_c): for t in [0, k-1], COMPUTE 90°-CCW-rotated offset (dr_t, dc_t) and PAINT (anchor_r + dr_t, anchor_c + dc_t) with color C (if in bounds). Row-0 markers discarded. Net: each orbit cell spawns k rotated copies around the 9-anchor.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
