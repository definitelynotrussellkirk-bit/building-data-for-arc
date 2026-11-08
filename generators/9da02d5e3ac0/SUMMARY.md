# 9da02d5e3ac0

Color-5 (gray) BACKGROUND grid (h, w~5-14) where EACH ROW contains ≥1 NON-5 CELL in some non-5 color (the row's marker value), with density ~0.15-0.5 of non-5 cells per row. Row palettes vary (uniform_per_row / all_distinct / biased — all using distinct non-5 colors). Rule: for EACH ROW independently, FIND the FIRST (leftmost) NON-5 CELL'S VALUE → the row's marker. For EVERY 5-CELL in that row, REPLACE it with the row's marker value. If a row has no non-5 cell, its 5s stay. Net: each row's 5-cells get repainted to match the row's first non-5 color; non-5 cells unchanged.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
