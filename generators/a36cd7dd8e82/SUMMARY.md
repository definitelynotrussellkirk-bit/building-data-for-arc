# a36cd7dd8e82

0-bg grid (h×w, ~4-7 by ~9-13) with: (a) a full-height vertical WALL of color 8 (cyan) at some column near the right side; (b) 1-3 'source' rows containing 1-3 non-zero non-8 cells at columns strictly LEFT of the wall. Other rows are empty. Rule: scan each row independently. For each non-0 non-8 cell, copy its color rightward into all subsequent columns of that row until just before the wall (or grid edge if no wall). Multiple cells in same row extend their smears; later cells overwrite earlier in column order. Wall preserved. Output: smeared rows + wall.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
