# 57870373a67e

0-bg grid (h, w~7-14) with 6-12 SPARSE COLOR-1 (blue) DOTS placed according to a layout pattern: scattered/clustered/row_focus/col_focus/diagonal/corners. At least one row AND one column has ≥2 blue dots with gap between them. Rule (BRACKETED-FILL WITH COLOR 8): for EACH 0-CELL at (r, c), check if there are COLOR-1 cells on BOTH SIDES in the SAME ROW (i.e., some c1 < c with g[r][c1]==1 AND some c2 > c with g[r][c2]==1) OR if there are COLOR-1 cells on BOTH SIDES in the SAME COLUMN. If yes, FILL the cell with COLOR 8 (cyan). Otherwise leave 0. Blue dots stay. Net: every 0-cell bracketed by blue in its row OR column gets painted cyan.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
