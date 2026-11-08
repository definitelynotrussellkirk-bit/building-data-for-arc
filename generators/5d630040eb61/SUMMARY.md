# 5d630040eb61

0-bg grid (h, w ~10-16) with multiple MULTICOLOR 8-conn OBJECTS (each a rectangular block in some base color, with some cells overpainted as color 8 / cyan). Objects are isolated by margin ≥ 2. There are 1-3 'BAD' objects (each has ≥ 2 cyan cells) and 1-3 'GOOD' objects (each has ≤ 1 cyan cell). Rule: extract 8-connected MULTICOLOR objects. For each object, count its cyan(8) cells. If count > 1 → erase the entire object (set all its cells to 0). Else (count ≤ 1) → keep the object as-is. Output: input with all 'bad' (≥2 cyan) objects erased.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
