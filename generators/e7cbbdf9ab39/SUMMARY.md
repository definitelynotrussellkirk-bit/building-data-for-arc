# e7cbbdf9ab39

0-bg grid (size varies by difficulty) with: (a) COLUMN MARKERS — 1-5 columns in range [1, w-2] are marked by COLOR 3 (green) cells at BOTH row 0 AND row h-1 of the same column (full top+bottom pair); (b) ROW MARKERS — 1-5 rows in range [1, h-2] are marked by COLOR 2 (red) cells at BOTH col 0 AND col w-1 of the same row (full left+right pair). All marker columns and rows are interior (≥2 cells from each edge). All other cells are bg-0. Rule (AT EVERY (ROW, COL) CROSSING OF PAIRED MARKERS, PLACE COLOR 8): identify the SET of PAIRED COLUMNS (those with color-3 at both top and bottom). identify the SET of PAIRED ROWS (those with color-2 at both left and right). For EACH (r, c) with r ∈ paired rows AND c ∈ paired cols: PAINT cell (r, c) with COLOR 8 (cyan). The original markers stay; other cells stay bg-0. Net: every intersection of a marked row and marked column becomes a cyan dot, drawing the row × column lattice of crossings.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
