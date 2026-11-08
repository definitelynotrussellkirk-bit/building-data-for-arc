# 5b35376e1fc9

Fixed 13×13 0-bg grid containing: (a) a CENTERED COLOR-2 (red) DIAMOND OUTLINE of radius 4 centered at (6, 6) — diamond boundary cells trace the manhattan-radius shape; (b) 2-4 EXTERIOR COLORED PIXELS on the GRID BORDER aligned with the diamond's horizontal/vertical AXIS (col 6 and row 6) in 4 distinct non-{0, 2} colors. Layout varies (cross / vertical / horizontal). Rule: for EACH exterior border PIXEL, cast a STRAIGHT RAY INWARD toward the grid center in its color. The ray travels through 0 cells until it reaches the diamond's OPPOSITE BOUNDARY (red color-2 cell) — at which point it stops. The exterior pixel and the diamond outline stay. Net: input is a red diamond outline + exterior border pixels; output adds colored rays from those pixels inward until they hit the diamond.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
