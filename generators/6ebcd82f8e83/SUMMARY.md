# 6ebcd82f8e83

0-bg grid (h, w~5-16) with 2-4 CELLS of a SINGLE NON-BG COLOR from {1..9} placed at the CORNERS of a SQUARE BBOX (side 3-min(h, w)-2, height == width). Always anchors at (r1, c1) and (r1+side, c1+side) with 50% chance of anti-diagonal corners (r1, c1+side) and (r1+side, c1) also set. Rule (DRAW X ACROSS SQUARE BBOX IN ORIGINAL COLOR): identify the 2+ NON-BG CELLS (all same color). COMPUTE their bbox (r1, c1, r2, c2) which is SQUARE (r2-r1 == c2-c1). EMIT a FRESH h×w OUTPUT GRID. PAINT BOTH DIAGONALS of the bbox in the ORIGINAL color — TL→BR diagonal AND TR→BL diagonal, forming an X. Off-diagonal cells stay 0. Net: 2-4 corner markers become an X spanning their square bbox.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
