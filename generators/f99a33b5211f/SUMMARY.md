# f99a33b5211f

0-bg grid (h, w~7-10) with ONE TARGET MARKER FRAME — a 3-cell L-shape anchored at a chosen origin (orig, vx, vy) painted in 3 marker colors {5, 6, 7} (per helpers/local_frame). The frame establishes a LOCAL COORDINATE SYSTEM where (2, 0) (2 cells along the x-axis from the origin) is IN-BOUNDS and INITIALLY BLANK. Rule (DRAW A 3-CELL X-AXIS BAR IN THE LOCAL FRAME): interpret the marker frame's 3 cells as (origin, x-direction vector, y-direction vector). Compute the LOCAL COORDINATE (2, 0) — i.e., origin + 2*vx + 0*vy. PAINT cells at LOCAL (0, 0), (1, 0), (2, 0) (a 3-cell run along the local x-axis starting from origin) with the FRAME's color or a specific color per puzzle convention. Net: the marker frame extends into a 3-cell bar in its declared x-direction.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
