# cef69adb634e

0-bg grid (h~9-11, w~13-15) with: (a) FOR EACH of colors {2, 3, 4}, EXACTLY 2 CELLS placed at DISTINCT ROWS AND DISTINCT COLUMNS (i.e., diagonal corners of a rectangle); (b) 1-4 DECOY cells in colors from {1, 5, 6, 7, 8, 9} at random empty positions. Each color may overlap rectangles but rectangle-outline paths can clobber decor — that's fine. Rule (PAINT RECT OUTLINES BETWEEN DIAGONAL CORNER PAIRS): For EACH color C ∈ {2, 3, 4}: if C has exactly 2 cells at (r1, c1) and (r2, c2) with r1 ≠ r2 AND c1 ≠ c2, PAINT the RECTANGLE OUTLINE through those 2 corners in color C — outline = top row, bottom row, left col, right col of the bbox (min, max)(rows/cols). Interior of the rect stays. Other colors (non-{2, 3, 4}) untouched. Net: each diagonal pair in 2/3/4 becomes a hollow rectangle outline.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
