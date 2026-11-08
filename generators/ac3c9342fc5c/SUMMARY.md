# ac3c9342fc5c

Input is 13 × w (w ~3-14). Rows 0-5 = TOP panel, row 6 = solid-color separator, rows 7-12 = BOTTOM panel. Each panel filled with some pattern (random/blob/stripes/checker/border/diagonal) at a chosen density in some color. Rule: output is 6 × w. For each (r, c) with r ∈ [0,5]: output[r][c] = 3 (green) IFF (input[r][c] == 0) XOR (input[r+7][c] == 0) — i.e. exactly ONE of the two panels has a zero at that cell (equivalently: the cells differ in zero/non-zero). Otherwise 0.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
