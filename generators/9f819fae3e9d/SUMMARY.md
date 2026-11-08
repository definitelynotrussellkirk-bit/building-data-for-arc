# 9f819fae3e9d

0-bg grid (h, w~8-11) with 1-3 HOLLOW 3×3 SAME-COLOR RINGS — each a 3×3 region where the 8 BORDER cells are painted in ONE NON-0 COLOR and the CENTER CELL is ZERO (a hollow ring). Ring centers are placed on a 4-cell stride grid (rows 1, 5, 9; cols 1, 5, 9) so rings don't touch. Each ring uses a distinct color from {1..8} (color (i%8)+1). Rule (FILL EACH HOLLOW 3×3 RING'S CENTER WITH RING COLOR): For EACH 3×3 WINDOW where all 8 BORDER CELLS are the SAME COLOR C and the CENTER cell is 0: PAINT the center cell with COLOR C. Cells outside such windows stay. Net: every hollow ring completes into a solid 3×3 patch of its ring color.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
