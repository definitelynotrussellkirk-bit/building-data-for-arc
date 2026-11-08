# 8a8f7fa44651

0-bg grid (h, w ~8-11) with 2-4 ISOLATED diagonal DOMINOES — each is 2 same-color cells at diagonal adjacency: (r, c) and (r+1, c±1). Different dominoes use distinct colors and have ≥2-cell buffer. Rule: for each cell (r, c), for each diagonal direction (dr, dc) ∈ {(1,1),(1,-1),(-1,1),(-1,-1)}: if input[r][c] is a non-bg color c0, input[r+dr][c+dc] is also c0 (forming a domino in that direction), input[r+2dr][c+2dc] is 0 (open end), and (r-dr, c-dc) is NOT c0 (so r,c is the outer end) → set output[r+2dr][c+2dc] = c0. Net effect: each diagonal domino grows by 1 cell at its OPEN END (the end not next to a same-color neighbor).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
