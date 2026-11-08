# 733d5c4a475a

0-bg grid (h, w~6-9) with: (a) EXACTLY TWO color-9 (maroon) MARKERS at distinct positions (a, b sorted by row then col) defining a translation VECTOR v = (b.r - a.r, b.c - a.c) with v ≠ (0, 0); (b) ONE small connected SHAPE (3-4 cells from a polyomino bank) in some non-{0, 9} color, placed in the upper-left region with at least one cell that translates in-bounds. Rule: read the vector v from the two 9-markers. For each non-9 shape, PAINT a TRANSLATED COPY at (cell + v) for each cell in the shape — using the shape's ORIGINAL color, skipping cells that fall OOB. The two 9-markers are ERASED in output (replaced by 0). Original shape stays + translated copy added. Net: each shape sprouts a ghost copy displaced by the 9→9 vector; the 9-markers themselves vanish.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
