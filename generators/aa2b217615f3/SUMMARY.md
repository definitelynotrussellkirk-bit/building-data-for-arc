# aa2b217615f3

0-bg grid (h, w~7-14) with: (a) ONE FULL-LENGTH COLOR-2 (red) EDGE LINE on ONE of the 4 GRID EDGES (top row, bottom row, left col, or right col); (b) 3-5 CONNECTED COLORED OBJECTS in DISTINCT non-{0, 2} colors, each a 1-3 cell shape from a small bank, scattered in the INTERIOR (not touching the red line). Objects are placed at non-touching positions (1-cell 8-conn buffer). Rule (SLIDE OBJECTS TOWARD THE RED LINE, STACKING): DETECT the red line's EDGE → DIRECTION (up/down/left/right TOWARD the line). SORT objects by DISTANCE to the line (closest first). For EACH object in that order: SLIDE the entire object (as a rigid group) toward the line by max amount until it hits the RED LINE or a PREVIOUSLY-PLACED object's cells. The line stays. Net: objects stack against the red line in distance-order.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
