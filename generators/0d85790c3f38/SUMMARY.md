# 0d85790c3f38

0-bg grid (h ∈ 5-8, w = 2*half_w with half_w ∈ 4-6 → w ∈ 8-12 EVEN, by difficulty) with: MARK_COUNT ∈ 4-7 SOURCE CELLS placed ONLY in the RIGHT HALF (cols half_w..2*half_w-1), each in a random color drawn from {1..9}. The LEFT HALF (cols 0..half_w-1) starts EMPTY. Rule (HORIZONTALLY MIRROR THE RIGHT HALF ONTO THE LEFT HALF, OVERWRITING ANY LEFT-HALF CONTENT; THE RIGHT HALF REMAINS UNCHANGED): For EACH cell (r, c) with c in 0..half_w-1: SET g[r][c] = g[r][w-1-c] (its mirror in the right half). The right half preserved. Net: input becomes left-right symmetric across the vertical axis at col half_w; left half is a mirror copy of right.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
