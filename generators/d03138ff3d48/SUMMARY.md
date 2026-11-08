# d03138ff3d48

h×w grid (h, w~3-6) with foreground non-bg cells in some PALETTE (warm/cool/broad/small) arranged in a LAYOUT (scattered/blob/diag/row/col/checker/frame). Column 0 is conditionally all-zero (col0_has_nonzero=false) or has at least one non-zero. ≥2 fg cells and ≥1 bg cell guaranteed; color 8 is never used in input (rule writes 8 for output). Rule (TASK-SPECIFIC OUTPUT NORMALIZATION): if column 0 of input has ANY NON-ZERO, produce a 2w-wide output with the LEFT HALF showing color-8 wherever the input has a 0 (a mask of zeros), and the RIGHT HALF being the original grid. ELSE (col 0 is all-zero), produce a 2w-wide output with the LEFT HALF being the original grid and the RIGHT HALF being the horizontal mirror. Net: input grid is doubled horizontally with color-8 mask of bg cells or its mirror, depending on col 0 contents.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
