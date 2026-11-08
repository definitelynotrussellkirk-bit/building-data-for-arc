# 72b99d3a9be8

0-bg grid (h, w~9-13) with ONE DIAGONAL PAIR of COLOR-1 cells: (a) DOWN-RIGHT pair: (r, c) and (r+1, c+1), or (b) DOWN-LEFT pair: (r, c+1) and (r+1, c). The pair is placed at interior position (r, c) with margins ≥3 from all sides (room for diagonal extension). Rule (DIAGONAL PAIR EXTENDS IN BOTH DIAGONAL DIRECTIONS, BOUNCING FROM COLOR-2 WALLS WHEN PRESENT): the pair defines a DIAGONAL DIRECTION (down-right or down-left). PROJECT the pair OUTWARD in BOTH diagonal directions (forward and backward), painting each diagonal cell COLOR 1, until either: (i) hitting a COLOR-2 WALL (the beam bounces — direction reverses or reflects per puzzle convention), or (ii) hitting the grid edge. Net: the diagonal pair extends into a full diagonal line spanning the grid.

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
