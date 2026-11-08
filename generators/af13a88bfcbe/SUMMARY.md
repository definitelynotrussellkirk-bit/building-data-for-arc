# af13a88bfcbe

0-bg grid (h~7-10, w~8-12) with 2-4 STRAIGHT LINE SEGMENTS (horizontal or vertical, length 2-4 cells) in DISTINCT colors. Lines are placed at spaced positions so they don't touch. Rule (MARK LINE ENDPOINTS WITH COLOR 8): for EACH non-zero CELL, COUNT its same-color CARDINAL (4-conn) NEIGHBORS. If the count is EXACTLY 1 (the cell has only one same-color neighbor — it's a line endpoint), RECOLOR it to COLOR 8 (cyan). Interior cells (2 same-color neighbors) keep their color. Singletons (0 neighbors) keep their color. Net: each line segment's two endpoints become cyan.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
