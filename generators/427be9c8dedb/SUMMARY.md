# 427be9c8dedb

0-bg grid (h ∈ 11-16, w ∈ 8-14) with 5-7 NON-ZERO COLORS at SCATTERED POSITIONS: palette drawn from one of {warm (3,4,6,9), cool (1,5,7,8), small (1..5), broad (1..9)}, expanded to ≥5 colors if needed. Counts drawn via _draw_counts using one of: default (random 22,12,6,4,2,2,2), wide_spread (30%, 15%, 7%, 4%, 2 cells), tight_spread (15% ± 5%), ascending (5%, 10%, 15%, ...). All 5+ NON-ZERO COUNTS are STRICTLY DISTINCT (no ties); bg=0 has the largest count overall. Cells placed at random free positions via random_free_cell. Rule (COUNT EACH NON-ZERO COLOR'S CELL FREQUENCY, SORT DESCENDING, OUTPUT THE 3RD, 4TH, 5TH MOST-COMMON COLORS AS A 3×1 COLUMN GRID): COUNT cells of each non-zero color. SORT colors by count DESCENDING. SELECT the 3RD, 4TH, 5TH entries (skipping the top-2). OUTPUT a 3-ROW × 1-COLUMN grid: row 0 = 3rd most-common color, row 1 = 4th, row 2 = 5th. Net: a frequency-based selection extracts the mid-tier colors and emits them as a vertical color triple.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
