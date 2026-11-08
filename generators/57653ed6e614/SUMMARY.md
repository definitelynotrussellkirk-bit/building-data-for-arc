# 57653ed6e614

0-bg grid with h ∈ {3..14} and ODD WIDTH w ∈ {5, 7, 9, 11, 13, 15} so the middle column mid = w//2 is well-defined: (a) ACTIVE ROWS — selected by one of 4 distributions (all_active / half_active / few_active / alternating_inactive). For each active row r: set g[r][0] = LEFT_COLOR and g[r][w-1] = RIGHT_COLOR (LEFT ≠ RIGHT, both non-{0, 5}); (b) OPTIONAL DECOY CELLS scattered in interior columns (1..w-2) at density 0..0.2 with random colors. If no rows are active, force row 0 active. Rule (FOR EACH ROW WITH NON-ZERO LEFT+RIGHT EDGES, CREATE LEFT/RIGHT BANDS SPLIT BY COLOR 5 AT THE MIDDLE COLUMN): for EACH ROW r where g[r][0] = lv ≠ 0 AND g[r][w-1] = rv ≠ 0: REPLACE the row: for c < mid: cell = lv; for c == mid: cell = 5; for c > mid: cell = rv. Non-active rows are unchanged (interior decoys stay). Net: each active row becomes a 3-zone band — left color, gray center, right color — replacing any interior decoys in that row.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
