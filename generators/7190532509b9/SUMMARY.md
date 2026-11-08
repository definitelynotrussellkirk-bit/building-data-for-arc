# 7190532509b9

0-bg grid (h, w~5-14) where each ACTIVE ROW has at COL 0 a NON-GRAY, NON-ZERO MARKER COLOR (per-active-row marker; diversity may be same / mixed / all-distinct across rows). The remaining cells of active rows (cols 1..w-1) contain 3-12 GRAY(5) CELLS placed in a chosen layout (random, cluster, one-per-row, column, diagonal, scattered) plus optional decor cells in other non-gray colors. Rule (PER-ROW RECOLOR GRAY → COL-0 MARKER): For EACH ROW r: let M = g[r][0] (the marker color). For EACH cell (r, c) with c ≥ 1: if cell value == 5 (gray), RECOLOR to M. Else, keep. Col 0 stays. Inactive rows normally stay all-bg. Net: gray cells inherit each row's left-edge marker color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
