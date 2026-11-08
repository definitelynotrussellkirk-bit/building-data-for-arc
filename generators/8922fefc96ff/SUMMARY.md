# 8922fefc96ff

0-bg grid (h~6-9, w~9-12) with 2-4 ACTIVE ROWS, each containing EXACTLY 2 COLOR-7 (orange) cells at distinct columns (c1, c2) with c2 ≥ c1 + 2 (gap of ≥1 bg cell between them). Plus 0-2 INACTIVE ROWS with a SINGLE orange cell (distractor) and 0-3 INACTIVE ROWS with non-orange distractor cells. Spans between endpoints in active rows are initially 0. Rule (PER-ROW HORIZONTAL ENDPOINT FILL): for EACH ROW, COUNT the COLOR-7 cells. If EXACTLY 2 (the endpoint pair) AND all cells BETWEEN them are 0, FILL the ENTIRE INCLUSIVE SPAN (cells from min_c to max_c in that row) with COLOR 7. Rows with 0, 1, or 3+ orange cells unchanged. Net: each row with exactly 2 orange endpoints gets filled between them; single-endpoint rows stay.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
