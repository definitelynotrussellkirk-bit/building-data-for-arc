# 727667a2d7b7

0-bg grid (h, w~10-22) containing 1-5 COLOR-6 (magenta) OBJECTS — each a small polyomino (3-4 cells from a shape bank: L, corner, T, S, square, L-tet, J, T-rot). Each object is placed at some interior position with sufficient padding for rotation to stay in-bounds. Each object has a SINGLE CONTROL CELL placed exactly ONE ROW ABOVE its bbox TOP-LEFT (at (r0-1, c0)) with VALUE ∈ {1, 2, 3, 4} (the rotation code: 1=identity, 2=cw90, 3=180°, 4=ccw90). Objects + their controls are mutually padded. Rule: for EACH magenta object, READ its control value at (r0-1, c0). ROTATE the object's normalized shape IN PLACE within its local bbox by the control code (1=identity, 2=cw90, 3=180°, 4=ccw90). The object stays color 6; the control stays in place. Net: each magenta polyomino rotates by its overhead control's quarter-turn count.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
