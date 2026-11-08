# 2f889ed81450

0-bg grid (h~7-9, w~8-10) with 1-3 ISOLATED non-bg SEED cells placed at interior positions (rows 2..h-3, cols 2..w-3) so each has at least 2 cells of bg margin in all 4 cardinal directions. Seeds are pairwise Manhattan-distance ≥ 5 apart so their distance-2 rays do not overlap. Each seed is in some non-bg color from a 2-8 palette. Rule: for every non-zero seed at (r, c) with color v, PAINT the four cells at distance 2 in the four cardinal directions: (r-2, c), (r+2, c), (r, c-2), (r, c+2) — each in color v. Cells out of bounds are skipped. The seed itself stays color v. Net: each colored seed sprouts 4 same-color satellite cells at Chebyshev-2 cardinal positions (like a sparse plus shape).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
