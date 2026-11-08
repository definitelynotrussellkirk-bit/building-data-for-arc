# 4f2480e18069

0-bg grid (h~7-10, w~8-12) with 2-4 SAME-COLOR HORIZONTAL ENDPOINT PAIRS, each on a DIFFERENT ROW, at columns (c1, c2) with c2 ≥ c1 + 2 (≥1 bg cell between them). Each pair uses a DISTINCT non-zero color from {1..9}. Active rows have exactly 2 cells in their color; the interval between is initially 0. Rule (FILL ROW INTERVAL BETWEEN ENDPOINTS): for EACH ROW with exactly 2 SAME-COLOR ENDPOINTS, FILL the INCLUSIVE INTERVAL between them (every cell from min_c to max_c in that row) with the pair's COLOR. Rows without endpoints stay 0. Net: each horizontal endpoint pair becomes a solid filled interval.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
