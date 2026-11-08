# a1f5c5bd7df9

0-bg grid (h ∈ 7-10, w = 2*half_w + 1 with half_w ∈ 4-6 → w ∈ 9-13 ODD so there's a center column at w//2) with: TARGET ∈ 3-8 SPARSE NON-BG CELLS placed at random LEFT-HALF positions (cols 0..half_w-1), each in a random color drawn from {1..9}. The RIGHT HALF (cols half_w+1..w-1) and the AXIS COLUMN (col half_w) start EMPTY. Rule (COMPLETE VERTICAL MIRROR SYMMETRY ACROSS THE CENTER COLUMN AXIS = W//2: FOR EACH NON-BG LEFT-HALF CELL AT (R, C) WITH COLOR k, PAINT g[R][W-1-C] = k; ALSO COPY BACK FROM ANY EXISTING RIGHT CELLS TO LEFT; CENTER AXIS COLUMN STAYS 0): For EACH non-bg cell at (r, c) with color k: COMPUTE mirror position (r, w-1-c). IF that mirror is bg (0): PAINT g[r][w-1-c] = k. The original left cells stay. Net: left-half pattern is reflected onto the right half across the central column axis.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
