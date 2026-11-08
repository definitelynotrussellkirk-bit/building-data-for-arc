# 69ebef53a2ac

0-bg grid (h~5-8, w~7-10) with 3-6 non-zero cells placed exclusively in the LEFT HALF (cols 0..w//2-1) in varied colors. RIGHT HALF (cols w//2..w-1) is all 0. Rule: for each cell (r, c) in output: if c < w//2 → keep input[r][c]. Else → mirror = input[r][w-1-c] (left-half value at the mirrored column). Net effect: the right half becomes a horizontal mirror image of the left half; result is a horizontally-symmetric grid.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
