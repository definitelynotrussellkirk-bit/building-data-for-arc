# ef8a47e301dd

Grid (h, w in [3,18], square or non-square) whose COLUMN 0 is painted a BG color (any of {0..9} except 2 and 4, and nonzero so it is visible), with the rest of the grid 0 — matching the canonical clean-column input. Rule: output column 0 = bg (g[0][0]), the anti-diagonal (r+c==h-1) = 2, the last row = 4, else 0. The output depends only on dims and the corner color; bg color and dimensions vary.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
