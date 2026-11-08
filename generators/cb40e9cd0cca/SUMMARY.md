# cb40e9cd0cca

0-bg grid (h~9-12, w~12-16) with 2-3 SOLID RECTANGLES drawn from a dims bank {(2,1),(1,3),(2,2),(2,3),(3,3),(3,4),(4,3)} — each rect has a DISTINCT cell count (e.g., 2, 3, 4, 6, 9, 12). Each rect uses a DISTINCT color from random_palette. Rects are non-overlapping with 1-cell padding. Rule (SORT BY SIZE ASC, HORIZONTAL GALLERY PACK): identify all SOLID rectangles. SORT by SIZE ASCENDING (color ASC as tiebreak). CROP each to its BBOX. PASTE the crops HORIZONTALLY with 1-COL GAPS in sorted order. Output WIDTH = sum of widths + gaps; HEIGHT = MAX height. Net: solid rects sorted small→large, horizontally packed.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
