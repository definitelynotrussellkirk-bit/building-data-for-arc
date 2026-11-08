# 55c08ab3ce73

0-bg grid (h~5-9, w = 2*half_w+1 with half_w~3-5) with: (a) a full-height color-5 DIVIDER column at col = half_w; (b) 3-6 scattered MOTIF cells in some non-{0, 5} color placed strictly LEFT of the divider (cols 1..half_w-1). Rule: detect the color-5 divider. For each non-{0, 5} cell at (r, c), MIRROR it across the divider: paint (r, 2*half_w - c) with the same color. Original cells + divider stay. Net: left motif gets a vertical mirror image on the right side.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
