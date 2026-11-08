# 5d06efc7bef9

Grid is 6 rows × 20 cols, divided into 3 panels of 6 cols each (cols 0-5, 7-12, 14-19) with single-column gaps. Each panel holds a single-color binary shape. Rule scale-normalizes each panel (downscale by 2 while possible), then outputs a 3×3 grid where cell (r, c) = 8 if panels r and c have the same scale-normalized shape signature, else 0. Diagonal always 8.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
