# caec0e511fe1

Grid (h, w~3-14) FULLY COLORED with one of 9 TEXTURE patterns (noise/sparse/blob/stripes/gradient/checkerboard/frame/ring/plus) drawn from a palette of 2-6 non-0 colors, plus 0-0.05 noise overlay. Any remaining 0-cells are filled with palette[0]; if monochrome after that, two corners are forced to different colors. Every cell is guaranteed non-zero. Rule (ADD MIRRORED 1-CELL BORDER): EMIT an (h+2)×(w+2) OUTPUT. PASTE the input at rows 1..h, cols 1..w. For BORDER rows/cols: TOP row (row 0) cols 1..w mirror ROW 0 of input. BOTTOM row mirrors row h-1. LEFT col mirrors col 0. RIGHT col mirrors col w-1. The 4 CORNERS stay 0. Net: input grows by 1-cell mirrored frame around all sides, corners left as 0.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
