# 71b44cea4ed1

0-bg grid (h, w ~7-10) with 2-4 same-color DIAGONAL ENDPOINT PAIRS — each pair has 2 cells of the same color at positions (r-1, c-1) and (r+1, c+1), or (r-1, c+1) and (r+1, c-1) — i.e. the cells are 2 diagonal steps apart with a 1-cell GAP (the midpoint (r, c)) currently zero. Pairs use distinct colors. Rule: detect each same-color diagonal pair separated by 2 cells, and paint their MIDPOINT with the same color. Net: each pair becomes a solid 3-cell diagonal.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
