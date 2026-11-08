# 99a1cb372ca4

0-bg grid (h~8-11, w~9-12) with 2-3 SOLID FILLED RECTANGLES of size rh × rw (3..4 each, so each rect has a strict INTERIOR), each painted entirely in a DISTINCT non-0 color drawn from a shuffled palette {1..9}. Rectangles are placed at non-touching positions with 1-cell padding via _free (no two rectangles share cells or 4-edges). Rule (REPLACE EACH SOLID FILLED RECTANGLE WITH ITS BBOX-OUTLINE — KEEPING THE BORDER, ERASING THE INTERIOR): for EACH solid rectangular blob of color C: identify its bbox (r1, c1, r2, c2). KEEP the BORDER CELLS (top row r1, bottom row r2, left col c1, right col c2 of the bbox) in color C. CLEAR the INTERIOR (cells (r1+1..r2-1, c1+1..c2-1)) to bg-0. Other rectangles outside the current blob's bbox stay unchanged. Net: solid filled rectangles become hollow outlines of the same color and size; interiors become bg-0.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
