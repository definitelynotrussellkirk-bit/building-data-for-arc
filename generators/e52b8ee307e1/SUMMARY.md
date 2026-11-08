# e52b8ee307e1

0-bg grid (h×w, h=4..6, w=7..9) with SPARSE non-zero cells. 3-4 columns are 'active' (have ≥1 non-zero cell at random rows in random non-zero colors). Other columns are entirely zero (the columns-to-drop). Active cell colors drawn from varied palette. Rule: iterate over columns. Keep only columns where at least one cell is non-zero. Output: each row projected to the kept columns only (in original column order). Output height = h (unchanged); width = number of active columns.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
