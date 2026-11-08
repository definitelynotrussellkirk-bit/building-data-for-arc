# a23328d45092

0-bg grid (h, w ~7-11) split into FOUR QUADRANTS by ONE full-width row of 1s (sep_r) AND ONE full-height col of 1s (sep_c). Each quadrant has scattered cells in its own distinct color (4 distinct colors across all quadrants, from {2..9}). Densities vary. Rule: find sep_r (first row that's all 1s) and sep_c (first col that's all 1s). Compute quadrant dims (sep_r, sep_c). For each output cell (r, c) in the quadrant-sized output: look at the 4 stacked values TL=g[r][c], TR=g[r][sep_c+1+c], BL=g[sep_r+1+r][c], BR=g[sep_r+1+r][sep_c+1+c]. Pick the FIRST non-zero in order TL, TR, BL, BR. Else 0.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
