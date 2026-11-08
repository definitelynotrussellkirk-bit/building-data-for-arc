# 406402d6defb

0-bg grid (h, w~8-11) with: (a) EXACTLY ONE color-1 (blue) ANCHOR cell placed at the grid's central position (h//2, w//2); (b) ONE small connected BLOB of 2-4 cells in some non-{0, 1} color, placed in the upper-LEFT region of the grid so that the blob's POINT-REFLECTION across the anchor lands fully IN-BOUNDS in the lower-right region and does NOT overlap the original blob or the anchor itself. Rule: the color-1 cell at (ar, ac) is the ANCHOR. For every non-1 non-0 cell at (r, c) with color k, PAINT its POINT-REFLECTION at (2*ar - r, 2*ac - c) with color k. The original blob stays and the anchor stays color 1. Net: the small blob sprouts a same-color mirror copy rotated 180° around the blue anchor.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
