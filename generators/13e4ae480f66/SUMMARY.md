# 13e4ae480f66

0-bg grid (h~8-10, w~9-12) with SEVERAL COLOR-1 (blue) CONNECTED COMPONENTS: (a) 1-2 LEFT-EDGE shapes from a bank of 3 (vertical tri-line, 2×2 square, L-shape) with at least one cell at col 0; (b) 1-2 INTERIOR shapes from a bank of 3 (2×2 square, L-shape, horizontal tri-line) placed entirely in c ≥ 1 with 1-cell padding. Components are 4-conn isolated. Rule (BORDER-TOUCH RECOLOR): for EACH color-1 connected component, check if ANY of its cells has column 0. If yes (touches left border), RECOLOR the ENTIRE component to COLOR 4 (yellow). Otherwise keep it as color 1. Net: blue blobs touching col 0 turn yellow; interior blue blobs stay blue.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
