# 88fea6584461

0-bg grid (h = block_h = 3-4, w = 2*block_w + 1 with block_w=4-5) structured as TWO EQUAL-SIZE PANELS separated by a full-height COLOR-8 (cyan) DIVIDER column at col bw. (a) LEFT PANEL (cols 0..bw-1) is a BINARY 0/1 MASK with 4-7 color-1 (blue) cells; (b) RIGHT PANEL (cols bw+1..2*bw) contains 4-7 arbitrary non-{0, 1, 8} colored cells from a 5-color palette. Rule: use the LEFT PANEL as a BINARY MASK (color-1 = keep, 0 = clear). For EVERY CELL in the RIGHT PANEL at (r, c), check the CORRESPONDING LEFT cell at (r, c - bw - 1): if it's 1 (blue), KEEP the right cell's color; if it's 0, CLEAR the right cell to 0. Output: the right panel (cropped or in place) after the mask filter. Net: left binary mask filters the right color block, keeping only cells the mask permits.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
