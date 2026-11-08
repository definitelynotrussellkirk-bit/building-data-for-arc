# 20b53e0c4957

h×(3·pw+2) grid (0-bg) split into THREE pw-wide panels by full-height color-5 (gray) divider columns at cols pw and 2·pw+1 (h and pw both vary, incl. non-square panels). Panel A: SOLID h×pw block of color X. Panel B: same color X but with several cells REMOVED (set to 0) at random positions. Panel C: SOLID h×pw block of a DIFFERENT color Y. Rule: split panels at the 5-columns. Compute REMOVED positions = A_cells − B_cells (relative to A's bbox). Apply the same removals to C: for each removed (rel_r, rel_c), set C[bbox_c_r1+rel_r][bbox_c_c1+rel_c] = 0. Output = modified C (h×pw).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
