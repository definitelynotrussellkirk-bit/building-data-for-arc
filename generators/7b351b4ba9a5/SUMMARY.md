# 7b351b4ba9a5

0-bg grid (h~6-9, w~6-9) with 1-3 ENDPOINT PAIRS placed on DOWN-RIGHT DIAGONALS. Each pair places two SAME-COLOR cells at positions (r1, c1) and (r1 + span, c1 + span) with span ∈ [2..4] (i.e., the two endpoints sit on the same '\'-slope diagonal with at least one empty diagonal cell between them). Different pairs use distinct non-bg colors and do NOT share any diagonal cells in their guard region. Rule: for each pair of same-color cells lying on a down-right diagonal at (r1, c1) and (r2, c2) with r2 = r1 + d and c2 = c1 + d, FILL every diagonal cell between them — (r1+1, c1+1), (r1+2, c1+2), ..., (r2-1, c2-1) — with that color. Endpoints stay. Net: each pair becomes a continuous diagonal line of its color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
