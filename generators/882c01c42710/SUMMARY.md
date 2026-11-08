# 882c01c42710

0-bg grid (h, w~12-16) with: (a) ONE HORIZONTAL SEED SEQUENCE at some center-ish row cr — 3-4 consecutive cells (starting at random col h_start) painted in distinct colors from a 4-color palette (palette colors used in order); (b) ONE VERTICAL SEED SEQUENCE at some center-ish col cc — 3-4 consecutive cells (starting at random row v_start) painted in the same palette order. Both sequences lie on the SAME center row/col axes. Rule: identify the row with the most non-bg cells (the H-axis center row) and the col with the most (the V-axis center col). For each axis, CYCLE the seed sequence across the ENTIRE row/col — extending the palette pattern (in order) to all cells of that row/col on both sides of the seeds. Net: a small seed sequence on each axis becomes a full periodic stripe spanning the row and column.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
