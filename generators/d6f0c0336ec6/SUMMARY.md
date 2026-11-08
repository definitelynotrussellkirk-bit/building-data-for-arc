# d6f0c0336ec6

0-bg grid (h~7-9, w~7-10) with 2-4 HORIZONTAL ENDPOINT PAIRS — each pair is 2 same-color cells in the SAME ROW at columns (c1, c2) with c2 ≥ c1 + 2 (gap of ≥1 bg cell between them). Each pair uses a DISTINCT non-zero color. Pairs occupy DISTINCT ROWS. Cells between endpoints start as 0. Rule: for EACH ROW that contains EXACTLY 2 SAME-COLOR CELLS, FILL the ENTIRE SPAN between them (all cells at columns min_c..max_c in that row) with the PAIR's COLOR. The two endpoints stay; the 0 cells between become the same color. Net: each same-color horizontal endpoint pair becomes a solid horizontal line connecting them.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
