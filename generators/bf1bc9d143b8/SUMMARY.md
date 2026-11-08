# bf1bc9d143b8

0-bg grid (h~5-7, w~7-9) with 2-3 HORIZONTAL endpoint TRIPLETS: each is a (color, 0, color) pattern in some row at consecutive cols (c, c+1, c+2). Plus 1-2 isolated DISTRACTOR cells that have no matching neighbor. Different triplets use varied non-bg colors. Rule: for each (r, c) with input == 0, check: HORIZONTAL match — (r, c-1) and (r, c+1) are equal non-bg → fill (r, c) with that color. Else VERTICAL match — (r-1, c) and (r+1, c) are equal non-bg → fill with that color. Horizontal precedence (if both match with different colors, horizontal wins).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
