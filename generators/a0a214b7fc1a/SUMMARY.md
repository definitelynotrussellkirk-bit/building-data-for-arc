# a0a214b7fc1a

Small SQUARE 0-bg grid (n~3-5, h == w) with 2-4 distinct non-zero colors in a TEXTURE pattern (noise / sparse / blob / stripes / gradient / checkerboard / frame / ring / plus) — NOT 4-fold symmetric (so rotations differ visibly). 4n ≤ 30 constraint. Rule: TILE the input grid into a 4n × 4n OUTPUT GRID structured as a 2×2 ARRAY of BIG QUADRANTS, where each big quadrant is itself a 2×2 of small n×n TILES, and each tile uses a DIFFERENT ROTATION (identity, cw90, 180°, ccw90). The output thus has 16 small n×n tiles total, each a different rotation of the input. Net: n×n input becomes 4n×4n output as a self-tiled 4-rotation kaleidoscope.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
