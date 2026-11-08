# 24ef0b5ae2e1

0-bg grid (h, w ~11-15) with: (a) a CROSS — full row + full col both painted in `cc` (cross color, becomes mode color); (b) 4 SHAPES (one per quadrant) in 4 distinct non-cc colors, each fitting in 3×3 with non-trivial structure (≥2 cells, anchored at corners). Rule: detect the cross (mode color, full row + col). Crop each quadrant. Assemble the 4 quadrant shapes into a 6×6 output grid arranged as TL/TR/BL/BR in the same layout as their source quadrants. Net: a 6×6 mini-grid showing the 4 shapes packed at fixed corners.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
