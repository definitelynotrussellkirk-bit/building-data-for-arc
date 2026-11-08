# f20defd6ea3c

0-bg grid (h~4-6, w~5-7) with 1-3 NON-ZERO SEED CELLS in DISTINCT non-0 colors from {1..9}. Each seed is a single cell at a random interior position (not in the last row or column so there's room for the diagonal to extend). Rule (EACH SEED PAINTS A DOWN-RIGHT DIAGONAL OF ITS COLOR UNTIL THE GRID EDGE): For EACH SEED at (r, c) with color C: PAINT cells (r+1, c+1), (r+2, c+2), ..., (r+k, c+k) with color C until r+k or c+k goes out of bounds. The seed itself stays at C. Net: each seed emits a down-right diagonal ray of its color reaching the bottom or right edge.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
