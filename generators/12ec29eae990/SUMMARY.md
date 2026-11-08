# 12ec29eae990

0-bg grid (h~11-13, w~12-14) with: (a) ROWS 0 and 1 forming a TWO-ROW LEGEND — row 0 holds 2-3 TRANSFORM TOKENS from {2, 3, 4, 9} at distinct columns (2 = rotate-cw, 3 = rotate-180, 4 = transpose, 9 = identity), and row 1 holds the matching ANCHOR COLORS in the same columns (legend maps anchor-color → transform-token); (b) BODY (rows 2..h-1) contains ONE COLOR-5 (gray) MOTIF (2-4 connected cells, the TEMPLATE shape) plus 2-3 single ANCHOR CELLS in colors matching the legend's anchor colors, placed away from the motif. Rule: drop rows 0/1. For each ANCHOR CELL in the body, LOOK UP its legend transform (rotate-cw / rotate-180 / transpose / identity). TRANSFORM the color-5 motif's shape per the legend code, then STAMP the transformed shape AT the anchor's position, painted in the anchor's COLOR. Net: each anchor sprouts a transformed stamp of the gray motif in its own color.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
