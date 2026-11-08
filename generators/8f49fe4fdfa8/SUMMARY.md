# 8f49fe4fdfa8

Fixed 12×13 0-bg grid with: (a) ROW 0 HEADER — holes encoded as (holes+1) COLOR-1 cells at cols 0..n; (b) g[0][4] = 2 if vertical SYMMETRY required, else 3; (c) g[0][6] = TARGET COLOR. BODY contains 4 OBJECTS at FIXED POSITIONS spanning the 4 (holes, symmetry) combos in {(0, 0), (0, 1), (1, 0), (1, 1)}, each in a DISTINCT non-target color from {2..8}. Output uniq_out=25 (intrinsic — fixed object positions × 4 spec combos × colors). Rule (SELECT MATCHING OBJECT, SCALE 2× + RECOLOR): READ HOLES = (count of 1s in row 0 - 1); SYMMETRY = (g[0][4] == 2); TARGET_COLOR = g[0][6]. SELECT the BODY OBJECT matching (holes, symmetry). UPSCALE 2× and RECOLOR to TARGET_COLOR. EMIT the result. Net: header drives object selection by (holes, sym); output is upscaled in target color.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
