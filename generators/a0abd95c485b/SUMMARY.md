# a0abd95c485b

0-bg grid (h~5-7, w~8-10) with 2-3 HORIZONTAL COLOR-4 (yellow) PAIRS — each pair is 2 adjacent color-4 cells at (r, c) and (r, c+1) where 1 ≤ c ≤ w-3 (so both flanking cells c-1 and c+2 are in-bounds and remain 0). Each pair occupies a DISTINCT ROW (no two pairs share a row). Rule (FLANK WITH 9s): for EVERY (r, c) where g[r][c]==4 AND g[r][c+1]==4, set g[r][c-1] = 9 (maroon) AND g[r][c+2] = 9 — but only if both target cells are in-bounds AND currently 0. The color-4 pair stays. Net: each horizontal yellow domino gets flanked left+right by maroon cells.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
