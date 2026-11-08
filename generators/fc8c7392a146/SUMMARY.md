# fc8c7392a146

0-bg grid (h~8-10, w~14-18). ROW 0 is a LEGEND: 2-3 NON-ZERO cells at distinct columns (in left-to-right column order). Below row 0 (starting at row 2) the body contains EXACTLY ONE connected 4-conn SHAPE per legend color, each in the matching color, sized 3-5 cells. Shapes are 4-conn isolated from each other. Rule: (1) For each legend color, locate its body shape and CROP it to its bounding box. (2) CANONICALIZE the crop by taking the lex-min over six dihedral variants: identity, rotate-CW, rotate-180, transpose, flip-LR, flip-UD. (3) CONCATENATE the canonical crops horizontally in LEGEND ORDER (left-to-right column order of the row-0 cells) with a 1-cell gap of bg-0 between each pair. Output: a wide gallery strip of canonical shapes arranged in the legend's order.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
