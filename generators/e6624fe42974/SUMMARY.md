# e6624fe42974

0-bg grid (h~5-12, w~9-16) with: (a) ONE FULL-HEIGHT COLOR-8 (cyan) DIVIDER COLUMN at col gc (mid-grid so mirroring fits both sides); (b) 2-6 NON-{0, 8} MARKER CELLS scattered on the LEFT side of the divider (c < gc), each in a color from {1..9}\{0, 8}. RIGHT side (c > gc) starts all 0. Each left marker has a valid in-bounds mirror position. Rule (MIRROR LEFT-MARKER CELLS ACROSS 8-DIVIDER): For EACH LEFT-side non-{0, 8} marker at (r, c): COMPUTE mc = 2 * gc - c (mirror position on the right). PAINT g[r][mc] with the same color (overwriting the 0). Left markers, divider stay. Net: left-side markers reflect across the cyan divider to the right side.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
