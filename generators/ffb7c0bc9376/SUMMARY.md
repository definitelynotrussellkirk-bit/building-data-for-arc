# ffb7c0bc9376

0-bg grid (h×w, ~8-13 by ~8-13) with 2-5 COLOR PAIRS. Each pair: 2 cells of the same non-zero color sharing a ROW or a COLUMN with ≥1 empty cell between them. Different pairs use distinct colors. Pairs are placed so they don't interfere with each other. Plus 1-2 isolated decoration cells (no partner) to test selectivity. Rule: for each color, find its cells. If exactly 2 cells share a row, fill the row segment between them inclusive with that color. If they share a column, fill the column segment. Isolated cells with count != 2 are unchanged.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
