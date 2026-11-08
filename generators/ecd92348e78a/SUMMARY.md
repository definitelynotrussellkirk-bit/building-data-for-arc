# ecd92348e78a

0-bg grid (h in [6, 19], w in [6, 20]) with 2-5 non-bg colors. Each color owns a contiguous ROW BAND whose height is that color's bar height; within its band the color fills one contiguous run per row. Blocks may STACK: a later block's rectangle can carve an earlier block from an edge (never splitting a row into two runs), but every color keeps at least one cell in its band's top and bottom rows, so the bbox height of every color is exactly its band height. Band heights are DISTINCT across colors. Rule (BAR CHART OF BBOX HEIGHTS, SORTED DESC): for each non-bg color compute bbox-height = max_row - min_row + 1 over all its cells; sort colors by height DESC; output a (max_height) x N chart where column c is a vertical bar of height_c cells of color_c at the top, 0 below.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
