# 9e204e7ff3a2

0-bg grid (h ∈ 5-14, w ∈ 5-14, by difficulty) with: SPARSE NON-BG CELLS in 1-4 DISTINCT COLORS, placed at density 15-40% via fg_layout ∈ {random / cluster (Manhattan-centered) / row (one full row picked) / column / diagonal / blob (Chebyshev) / scattered (every other (r+c))} in candidates filtered by row_bias ∈ {top / bottom / spread}. The grid is INTENTIONALLY UD-ASYMMETRIC — at least one cell exists where the UD mirror position (h-1-r, c) is currently 0 (so the rule has visible effect). If natural placement happens to be UD-symmetric, the generator forces one asymmetric cell. Rule (COMPLETE TOP-BOTTOM (UD) SYMMETRY — FILL EVERY BG CELL WHOSE UD MIRROR IS NON-BG WITH THE MIRROR'S COLOR): For EACH (r, c) where g[r][c] == 0: COMPUTE the UD mirror (h-1-r, c). IF the mirror cell is non-bg: PAINT g[r][c] with the mirror's color. ORIGINAL non-bg cells preserved. Net: every cell gets the color of itself OR its UD mirror (whichever is non-bg first); the grid becomes UD-symmetric — gaps in the top half are filled from the bottom half and vice versa.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
