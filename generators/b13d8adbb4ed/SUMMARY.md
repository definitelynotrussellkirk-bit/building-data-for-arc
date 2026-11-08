# b13d8adbb4ed

0-bg grid (h~8-10, w~9-11) with: (a) cell (0, 0) holds a CONTROL CODE in {1, 2, 3, 4, 5}; (b) EXACTLY ONE isolated ASYMMETRIC SHAPE (3-6 cells from a bank of 9 asymmetric tetro/pent shapes) in some non-control color elsewhere in the grid (rows 2+, cols 2+) with 1-cell padding. Rule (CONTROL-CODE TRANSFORM CROP): CLEAR cell (0, 0). CROP the remaining grid to its non-zero CONTENT BBOX (the shape's bbox). APPLY the TRANSFORM indexed by the control code: 1 = identity, 2 = rotate CW 90°, 3 = rotate 180°, 4 = rotate CCW 90°, 5 = flip horizontal. OUTPUT: the cropped, transformed shape. Net: code cell at (0, 0) picks the geometric transform applied to the cropped asymmetric shape.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
