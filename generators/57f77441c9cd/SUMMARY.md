# 57f77441c9cd

0-bg grid where: col 0 has a vertical color-5 SEGMENT (rows 0..gh-1 are 5, rest 0). Cols cs..w-1 (cs ≥ 2) each contain non-{0, 5} color cells (typically full columns). Cols 1..cs-1 are all 0. Rule: detect gh (length of col-0 5-segment), cs (first non-{0, 5} col). Build OUTPUT col oc = cs - 1: for each row r, set g[r][oc] = g[0][cs + (r // gh) % n] where n = w - cs (number of right cols, cycling through them). Output preserves col 0 5-segment, clears other cells.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
