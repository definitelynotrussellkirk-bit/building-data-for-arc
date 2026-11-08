# 156db8fda1bb

0-bg grid (h~5-10, w~8-14) with 3+ ACTIVE ROWS each containing 2-many NON-BG CELLS in a SINGLE color C (from {1..9}\{0, 2}) arranged via one of 5 ROW PATTERNS (scattered/endpoints_only/ascending/many_cells/alternating). Endpoint separation (near/medium/far) and intermediate density (0..0.4) vary. Leftmost and rightmost non-bg cells in each active row are ≥2 cols apart. Rule (FILL BETWEEN ROW EXTREMES WITH 2): For EACH ROW r: find the LEFTMOST (c_min) and RIGHTMOST (c_max) non-bg cells. For EACH cell (r, c) with c_min < c < c_max AND g[r][c] == 0: PAINT g[r][c] = 2 (red). Existing non-bg cells stay. Net: each row gets red interior filling between its extreme non-bg cells.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
