# 20c0f50887ff

0-bg grid (h~8-10, w~9-11) with: (a) 1-2 COLOR-5 (gray) WALL SEGMENTS as horizontal or vertical line segments (3-5 cells long) placed in the interior; (b) 2-3 single SEED CELLS in DISTINCT non-{0, 5} colors placed at random non-wall positions, non-4-touching each other. Rule: for EVERY non-{0, 5} SEED cell, emit 4 CARDINAL RAYS (up, down, left, right) in the SEED'S COLOR. Each ray walks from the seed until it hits a 5-wall cell, the grid EDGE, or the original grid boundary, painting every empty cell along the way. Walls STOP the ray (wall stays gray). Multiple seeds' rays may overlap — last-paint wins or order-independent depending on layout. Net: each colored seed sprouts a cardinal color-cross extending until walls/edges.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
