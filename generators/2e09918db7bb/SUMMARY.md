# 2e09918db7bb

0-bg grid (size varies). Cell (0,0) is a DIRECTION MARKER (1=left, 2=right, 3=up, 4=down). Some color-8 cells form fixed WALLS (random line segments). Several colored polyominoes are scattered as separate components. Rule: drop the marker cell, then slide EVERY non-wall object as a rigid 4-connected component in the marker's direction until it is blocked by a wall, another object, or the grid edge (gravity settling, leading objects move first). Grid size, direction, wall layout and the object set all vary freely, and at least one object always has clear runway so the output differs from the input (was a fixed 9x12 grid with 6 hardcoded variants).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
