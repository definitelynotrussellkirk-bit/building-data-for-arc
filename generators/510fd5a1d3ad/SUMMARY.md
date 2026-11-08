# 510fd5a1d3ad

0-bg grid with: (a) one SOURCE TEMPLATE — a small connected shape in colors from {5, 6, 7} (3-5 cells); (b) 2-3 ANCHOR PAIRS scattered elsewhere — each anchor is a color-9 (maroon) cell with a color-in-{1, 2, 3, 4} cell immediately to its LEFT (at column anchor_col - 1). The left-cell value k encodes the transform: 1=identity, 2=rot-CW, 3=rot-180, 4=rot-CCW. Rule: extract the source — the largest 4-conn component using colors {5, 6, 7}. Normalize to bbox corner. For each anchor (a color-9 cell preceded by a {1..4} cell to its left), apply transform (k - 1) to the source and stamp the result at the anchor's position. Output: empty grid + stamped, transformed source copies at each anchor.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
