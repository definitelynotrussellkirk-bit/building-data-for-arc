# 530b63eb8e59

0-bg grid (h~6-8, w~8-10) with 2 single SOURCE CELLS in distinct non-zero colors from {2, 3, 4, 5}, placed at hardcoded positions (1, 3) and (4, 2). NOTE: positions hardcoded — diversity is intrinsic-mid. Rule: for EACH EMPTY (0) CELL, FIND all SOURCES that are VISIBLE (same row or column, no non-zero between the cell and the source). For the cell: if EXACTLY ONE color is visible (only one source on its axes), PAINT it that color; if ≥2 DISTINCT colors are visible, PAINT it COLOR 8 (cyan); if zero visible, leave as 0. Sources stay. Net: empty cells fill with the unique visible source color, or cyan for intersections of multiple source axes.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
