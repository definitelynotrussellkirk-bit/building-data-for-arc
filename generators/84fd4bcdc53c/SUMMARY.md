# 84fd4bcdc53c

0-bg grid (easy ~8x10 -> hard up to ~19x20) with 1-4 distinct non-bg colors (scaled by difficulty), each with 2-4 ENDPOINT cells placed at DISTINCT rows AND distinct cols (so consecutive endpoints define a clear L-bend). Rule: for each color, sort its cells in scan order (row-major). Connect consecutive cells with an L-PATH: first horizontal segment from (r1, c1) to (r1, c2), then vertical segment from (r1, c2) to (r2, c2). Paint every cell along the L-path with that color. Net: endpoints become connected by staircase L-paths.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
