# 8ed0a21826ed

0-bg grid (h, w~14-16) with: (a) ONE SOLID RECTANGLE (3×4 to 5×6) in some non-zero rect_color at a random interior position; (b) 2-4 SMALL DOT CELLS placed OUTSIDE the rectangle at positions that are HORIZONTALLY or VERTICALLY ALIGNED with the rectangle's edges (with ~3-cell gaps). Dots use distinct non-{0, rect_color} colors from a 4-color palette. Rule: for EACH dot, determine its ALIGNMENT direction to the rectangle (does it share a row or col with the rectangle's boundary?). CAST a BEAM from the dot's position TOWARD the rectangle in the dot's color, filling every bg cell along the straight-line path between the dot and the rectangle's nearest face. The rectangle and the dots stay. Net: each dot shoots a colored beam toward the largest rectangle.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
