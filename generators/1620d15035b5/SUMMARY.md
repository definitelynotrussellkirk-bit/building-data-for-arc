# 1620d15035b5

0-bg grid where: (a) row 0 has K color-1 cells (the AREA target K); (b) col 0 has W color-3 cells (the WIDTH target W); (c) 2-4 OBJECTS in non-{1, 3} colors scattered in interior cells (not in row 0 or col 0). EXACTLY ONE object has size == K AND bbox width == W. Other objects are distractors with size != K OR width != W. Rule: read K from row 0 (count of 1s), W from col 0 (count of 3s). Find the unique object with size K AND width W. Paint it in color 8 on a fresh canvas; all else becomes 0.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
