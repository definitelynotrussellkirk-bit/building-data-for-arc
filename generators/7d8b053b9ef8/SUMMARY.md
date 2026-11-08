# 7d8b053b9ef8

0-bg grid with: (a) a CONTROL cell in {3, 4, 6, 7} placed at any position (often top-left corner); (b) one color-1 (blue) shape with ≥3 cells; (c) one color-2 (red) shape with ≥3 cells. Both shapes' NORMALIZED cells (cells shifted so min row, col = 0) partially overlap (have at least one common cell AND each has cells not in the other). Rule: read control. Compute boolean op on normalized cell sets: 3 → union, 4 → intersection, 6 → XOR, else → blue minus red. Output is the resulting cells painted 8 and cropped to their bbox.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
