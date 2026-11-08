# 96e581ff27a4

0-bg grid (h~5-7, w~7-9) with: (a) cell (0, 0) holding a DIRECTION CODE ∈ {1, 2, 3, 4} (1=up, 2=right, 3=down, 4=left); (b) 2-3 INTERIOR CELLS placed at rows 1..h-2, cols 1..w-2 in distinct non-zero colors. Rule: READ the CODE at (0, 0) and determine shift vector (dr, dc): 1→(-1, 0), 2→(0, +1), 3→(+1, 0), 4→(0, -1). Build an EMPTY OUTPUT GRID. For EVERY non-(0,0) cell, COMPUTE its shifted position (r+dr, c+dc) and PAINT that cell with the marker's value. The code cell is consumed. Net: code at origin dictates direction; marker cells shift uniformly by 1 cell in that direction.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
