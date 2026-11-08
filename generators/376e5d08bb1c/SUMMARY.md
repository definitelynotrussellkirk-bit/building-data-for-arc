# 376e5d08bb1c

Grid where every column has a SEED of 1-3 non-zero values starting from row 0 (contiguous prefix). Below the seed prefix, all cells are 0 — the area the rule will fill. Different columns may have different seed lengths. Rule: for each column c, find the contiguous-from-top non-zero prefix as the seed pattern. Repeat that seed downward periodically to fill the column for all h rows. Output has the same dims as input but with all 0-cells in each column replaced with the corresponding seed value.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
