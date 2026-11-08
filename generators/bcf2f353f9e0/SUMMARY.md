# bcf2f353f9e0

0-bg grid (h~7-10, w~10-14) with: (a) ONE COLOR-2 (red) CONNECTED COMPONENT placed at the LEFT side (col c0 ∈ 0..2) of the grid, drawn from a 3-shape bank (small L/T-tetro shapes); (b) blocker_kind ∈ {wall, edge}: if WALL, a full-height COLOR-8 (cyan) WALL is placed at col wall_c (at least 2 cells right of the red); if EDGE, no wall, the grid edge acts as the right boundary. Rule (SLIDE RED RIGHT UNTIL BLOCKED): identify the COLOR-2 component. SLIDE it RIGHTWARD as a rigid body until ANY of its cells WOULD HIT (a) the GRID's RIGHT EDGE (col w) or (b) a COLOR-8 WALL cell. STOP at the first contact (translated cells stay in bounds and don't overlap walls). Walls stay. Net: red component shifts right as a unit until obstructed.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
