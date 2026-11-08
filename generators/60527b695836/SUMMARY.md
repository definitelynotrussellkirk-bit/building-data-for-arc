# 60527b695836

0-bg grid (h~5-10, w~6-12) with 2-4 L-TROMINO PATTERNS of color 8 (cyan). Each L is a 2×2 sub-block with 3 cells of color 8 and 1 cell of 0 — the variant determines which corner is missing: missing_BR, missing_BL, missing_TR, missing_TL (or mixed across the grid). Patterns are separated by ≥ 2-3 cells. No color-1 in input. Rule: scan every 2×2 sub-block of the grid. If exactly 3 of the 4 cells are color 8 AND the remaining cell is 0, SET that 0-cell to color 1 (blue) — completing the L into a solid 2×2 (3 cyan + 1 blue). Net: each L-tromino sprouts a blue cell in its missing corner.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
