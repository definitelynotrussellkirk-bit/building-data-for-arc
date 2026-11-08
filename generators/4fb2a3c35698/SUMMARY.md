# 4fb2a3c35698

0-bg grid (h~7-10, w~7-10) with: (a) ROW 0 SRC COLORS — at columns 0..n-1 (n=3-5 pairs), row 0 holds SOURCE colors drawn from a palette of n+1 distinct non-0 values; (b) ROW 1 DST COLORS — at the same columns, row 1 holds TARGET colors (each colors[(c+1) % len(palette)] cyclically — paired src→dst mapping); (c) BODY rows 2..h-1 — contain several separated small objects/line-like blobs in the SOURCE colors from the palette[:n] mapping domain, with every source color represented at least once. Rule (APPLY THE TOP-2-ROW COLOR SUBSTITUTION MAP ONLY TO ROWS 2 AND BELOW): READ row 0 and row 1 to build a SRC→DST MAP {g[0][c] → g[1][c] for c with non-0 g[0][c]}. For EACH cell in ROWS 2..h-1: if the cell's value is a SRC in the map, REPLACE it with the corresponding DST. Cells with non-mapped values stay. Rows 0 and 1 (the legend) stay unchanged. Net: the body is recolored by the top-2 legend.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
