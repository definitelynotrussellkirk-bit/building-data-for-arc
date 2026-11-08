# da4a2278f620

Square N×N (6 ≤ N ≤ 9) 0-bg grid with 3-5 non-zero source cells in distinct colors at scattered positions. Each source cell's anti-diagonal mirror image is blank (so the rule can fill it). Rule: for each cell (r, c), if v == 0 AND the anti-diagonal mirror cell (N-1-c, N-1-r) has value ref != 0, then fill with ref. Otherwise preserve. Effectively each non-zero source cell gets reflected across the anti-diagonal.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
