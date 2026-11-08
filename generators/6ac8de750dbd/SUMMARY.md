# 6ac8de750dbd

0-bg grid (h, w ~9-12) with 2 color-1 (blue) 4-conn objects of different sizes plus a color-5 (gray) distractor single cell. Rule: identify all color-1 objects, pick the LARGEST by cell count, compute its bbox (r1, c1, r2, c2), and paint the 4 BBOX CORNERS (r1, c1), (r1, c2), (r2, c1), (r2, c2) with color 2 (red). Note: those corners may already be color 1 if the object touches its bbox — they get overwritten to 2. Rest of grid stays unchanged.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
