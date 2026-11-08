# 87739bb6a3d1

0-bg grid (h~7-9, w~7-9) with 2-4 ENDPOINT PAIRS: each pair places two SAME-COLOR cells in the SAME COLUMN at rows r1 < r2 with r2 ≥ r1 + 2 (so there is at least one empty cell strictly between them). Different pairs use distinct columns and distinct non-bg colors. Cells between the endpoints in each pair are 0. Rule: for every column that contains exactly two same-color cells at rows r1 and r2, FILL every cell at rows r1+1 .. r2-1 in that column with that color, bridging the gap into a solid VERTICAL BAR. Endpoints stay; non-pair columns stay 0. Net: each pair of isolated endpoints becomes a continuous vertical line.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
