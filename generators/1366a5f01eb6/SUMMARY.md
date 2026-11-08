# 1366a5f01eb6

0-bg grid (h~5-7, w=9) with: (a) FULL-HEIGHT GRAY (color 5) DIVIDER COLUMN at column 4 (the exact middle); (b) LEFT SIDE (cols 0..3) has 2-3 ISOLATED NON-{0, 5} CELLS placed at distinct random positions, each painted with a color drawn from {1, 2, 3, 4, 6, 7, 8, 9}; (c) RIGHT SIDE (cols 5..8) starts ENTIRELY bg-0. Left cells are constrained to fit so their right mirror lands in-bounds. Rule (MIRROR LEFT-SIDE COLORS ACROSS THE GRAY DIVIDER): identify the full-height GRAY (color 5) DIVIDER COLUMN at col div = 4. For EACH non-{0, 5} CELL at position (r, c) where c < div: COMPUTE the MIRROR position (r, 2*div - c) on the right side. IF the mirror cell is currently bg-0: PAINT it with the SAME COLOR as the source. If the mirror cell is already non-0, SKIP. The divider and the source left-side cells stay unchanged. Net: the left half's scattered colors are reflected across the gray divider to populate the right side, producing left-right mirror symmetry.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
