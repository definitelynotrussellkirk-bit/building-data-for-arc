# b7d1baa57fb4

0-bg grid (h~8-14, w~10-16) with: (a) ONE MIRROR AXIS COLUMN at axis_col (3..w-4) — 1-3 COLOR-8 (cyan) CELLS placed at random rows on this column (NOT a full 8-column, just markers); (b) 5-10 SCATTERED NON-ZERO CELLS in colors from palette (warm/cool/broad/primary) on ONE SIDE of the axis (left OR right). Cells are not on the axis column. Rule (IDENTIFY 8-AXIS, MIRROR NON-ZERO CELLS, FILL AXIS): identify the AXIS COLUMN (unique col containing ≥1 color-8). For EACH 0-cell at (r, c) with c ≠ axis_col: COMPUTE MIRROR position (r, 2*axis_col - c). If the MIRROR cell is non-zero, COPY it to (r, c). AXIS COLUMN becomes ENTIRELY COLOR-8 (every cell on the axis col is filled with 8). Net: scattered cells reflect across the 8-axis; axis column becomes solid cyan.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
