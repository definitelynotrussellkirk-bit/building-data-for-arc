# 1952043bdb9d

0-bg grid (h~5-7, w~6-8) where 3-4 RANDOMLY-CHOSEN COLUMNS each have 2-3 NON-BG CELLS at random rows in various colors drawn from {2..9}. Other columns may have 0 or 1 single cells (at ~50% chance). The ≥3 active columns ensure the output differs from input. Rule (PER-COLUMN, KEEP ONLY THE BOTTOMMOST NON-BG CELL): For EACH COLUMN c in [0, w-1]: find the MAXIMUM ROW r where g[r][c] ≠ 0 (the bottommost non-bg cell). KEEP the cell at (r, c) with its color. ERASE all OTHER non-bg cells in column c (set them to 0). Columns with no non-bg cell stay all 0. Net: each column collapses to its bottom-most painted cell only.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
