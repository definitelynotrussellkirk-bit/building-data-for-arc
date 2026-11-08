# 20fa0e6e2e3b

0-bg grid (h, w~8-13) with HARDCODED LAYOUT: (a) COLOR-7 SOLID 2×3 RECT at (0..1, 0..2) (6 cells, largest); (b) COLOR-8 SOLID 3×3 RECT at (h-3..h-1, w-3..w-1) (9 cells); (c) COLOR-2 L-SHAPE at random interior position (r, c) with cells (r, c), (r+1, c), (r+1, c+1) — 3 cells, always smallest. Hardcoded shapes + 7 and 8 fixed positions; only the L-shape position varies. Output uniq_out=1 — always emits the same L-shape 2×2 bbox in COLOR-2 (intrinsic — fixed smallest shape). Rule (CROP SMALLEST CONNECTED OBJECT TO BBOX): identify all NON-BG connected components. FIND the SMALLEST by cell count. CROP it to its BBOX. EMIT the cropped subgrid. Net: smallest object's bbox crop is the output.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
