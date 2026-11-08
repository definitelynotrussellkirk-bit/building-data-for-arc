# db67c3d76937

0-bg grid (h×w, ~7-9 by ~9-11) with EXACTLY 2 pairs of cells: one VERTICAL pair of color A (2 cells in same column, different rows) and one HORIZONTAL pair of color B (2 cells in same row, different columns), where A ≠ B and A, B ≠ 9. The two spans (vertical line A, horizontal line B) cross at exactly one cell. Rule: for each non-bg color with exactly 2 cells, compute the SPAN (inclusive line of cells from one endpoint to the other, horizontal if same row, vertical if same column). Paint each span cell with that color. If any cell is in 2+ spans (intersection), overwrite with color 9 (maroon). Output: a cross pattern with 9 at the intersection.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
