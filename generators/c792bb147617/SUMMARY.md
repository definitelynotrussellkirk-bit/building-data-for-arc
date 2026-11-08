# c792bb147617

0-bg grid (h~8-14, w~8-14) containing 2-4 SPARSE color-1 (blue) PIXELS placed in the interior (not on outermost rows/cols) at positions Chebyshev-separated by ≥3 cells (so each blue's compass-neighbors don't overlap any other blue or its compass spray). Each blue pixel's 4 cardinal neighbors are initially bg. Position bias varies: scattered / row_aligned / col_aligned / diagonal / corners / centered. Rule: for EVERY color-1 (blue) pixel at (r, c), PAINT its compass NEIGHBORS: UP (r-1, c) → color 2 (red); DOWN (r+1, c) → color 8 (cyan); LEFT (r, c-1) → color 7 (orange); RIGHT (r, c+1) → color 6 (magenta). The blue pixel itself STAYS blue. Net: each blue dot sprouts a 4-color compass cross around itself.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
