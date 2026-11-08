# 8c6b703c91e5

0-bg grid with a full color-5 divider (either a complete row or a complete column). Orange (color 7) cells lie on ONE side of the divider; the OTHER side may carry decorations in colors ≠ {0,5,7,1}. Rule: detect whether the divider is row-shaped or col-shaped (full rows tried first); for each color-7 cell at (r,c), compute its reflection across the divider: if row-divider at row d, mirror to (2d-r, c); if col-divider at col d, mirror to (r, 2d-c). Paint color 1 (blue) at the reflected position IF in-bounds AND the cell is currently 0 (existing decorations are preserved, not overwritten). Original 7s and all other cells are kept as-is.

Kind: `per_puzzle`. Imported version: `1.2.1`.
Approval is derived by the catalog from current code and retained evidence.
