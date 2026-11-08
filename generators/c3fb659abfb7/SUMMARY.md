# c3fb659abfb7

0-bg grid (h×w, ~8-12 by ~9-12) with: (a) EXACTLY 2 color-9 (maroon) MARKER cells at distinct positions defining a translation vector (the markers are sorted by reading order, vector = second - first); (b) a connected SHAPE of 2-4 cells in some non-{0, 9} color near one of the markers. Translated copies must fit in-bounds. Rule: locate the 2 color-9 markers. Compute (dr, dc) = marker_2 - marker_1. For each non-0 non-9 cell, paint that cell color at original position AND at (r+dr, c+dc) on a fresh canvas. Markers do NOT appear in output.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
