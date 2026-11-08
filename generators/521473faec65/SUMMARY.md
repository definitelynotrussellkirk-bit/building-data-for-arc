# 521473faec65

0-bg grid (h~7-9, w~9-11) with 2-3 SOLID RECTANGLES (each ≥2×2) at scattered positions (typically near corners). Each rectangle in a DISTINCT non-zero color. Rectangles don't touch. Rule: for EACH SOLID RECTANGLE, compute its bbox (r1, c1, r2, c2) and color. For EVERY CELL (r, c) inside that bbox, KEEP it at the rectangle's color IFF (r - r1 + c - c1) is EVEN; otherwise SET it to 0. Apply a CHECKERBOARD MASK starting at top-left corner. Net: solid rectangles become checkerboarded — half stay, half clear in diagonal pattern.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
