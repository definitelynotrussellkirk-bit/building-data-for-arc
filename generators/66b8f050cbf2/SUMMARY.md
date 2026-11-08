# 66b8f050cbf2

0-bg grid (h~5-7, w~7-9) with: (a) cell (0, 0) holding a CMD value ∈ {1, 2, 3, 4} (1=up, 2=right, 3=down, 4=left) — the direction code; (b) 2-3 single MARKER CELLS in distinct colors from {5..9} placed at INTERIOR positions (rows 1..h-2, cols 1..w-2). Markers are placed with spacing so their post-shift positions stay in-bounds. Rule: READ the CMD at (0, 0) and determine the shift VECTOR: 1→(-1,0), 2→(0,+1), 3→(+1,0), 4→(0,-1). Build an EMPTY OUTPUT GRID. For EVERY non-cmd (value ≥ 5) cell, COMPUTE its shifted position (r+dr, c+dc) and PAINT that cell with the marker's value. The cmd cell itself is consumed (not painted in output). Net: cmd at origin dictates direction; markers shift uniformly by 1 cell in that direction; output is empty + shifted markers.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
