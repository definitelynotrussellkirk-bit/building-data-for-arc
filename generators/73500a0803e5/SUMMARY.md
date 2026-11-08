# 73500a0803e5

0-bg grid (h~4-6, w~5-7) with: (a) ROW 0 has 2-4 COLUMN MARKERS painted color 8 (cyan) at random column positions; (b) ROWS 1+ contain random non-8 color cells at ~60% density. Rule: detect which columns have a color-8 marker in row 0. Output is (h-1) × N_marked sub-grid: take ROWS 1..h-1 of the input, and KEEP ONLY the marked columns (in their original left-to-right order). Net: filter body cells through the column-marker mask.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
