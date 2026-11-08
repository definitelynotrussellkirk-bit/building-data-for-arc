# 22ee9e5c3a9a

0-bg grid (h, w~8-13) with 2-5 STRAIGHT COLOR-3 (green) LINES, each of length 3-6 cells, all HORIZONTAL (each on its own row) or all VERTICAL (each in its own column) — generator picks orientation per sample. Lines are placed on distinct rows/cols with no row/col overlap (so endpoints are unambiguous). Rule: identify every GREEN CONNECTED COMPONENT that is a STRAIGHT LINE of length ≥3 (horizontal or vertical). For each such line, find its TWO ENDPOINTS (the two cells at the ends — col c0 and col c2 for horizontal, row r0 and row r2 for vertical). RECOLOR those two endpoint cells to COLOR 2 (red). The interior cells of the line stay green. Net: each green straight line gets its two ends repainted red; interior stays green.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
