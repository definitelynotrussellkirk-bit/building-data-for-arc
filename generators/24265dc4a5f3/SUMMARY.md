# 24265dc4a5f3

Grid (size varies) with: (a) ONE COLOR-8 (cyan) BAR of varied length/position, either HORIZONTAL or VERTICAL; (b) 3+ COLORED PIXELS in non-{0, 8} colors placed at varied positions beyond the bar in rows/columns the bar covers. Rule (PROJECT TO BAR-ADJACENT ROW/COL): identify the CYAN BAR's orientation. For EACH COLORED PIXEL at (pr, pc): if the bar is HORIZONTAL (row r), PROJECT the pixel to the cell DIRECTLY ADJACENT to the bar in the pixel's column — i.e., paint (r-1, pc) or (r+1, pc) depending on which side the pixel is on, in the pixel's color. If the bar is VERTICAL, project to (pr, c-1) or (pr, c+1). The original pixel may be cleared or kept. Net: scattered pixels collapse to projections one cell from the cyan bar.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
