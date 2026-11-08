# ae370359ef71

0-bg grid (h~5-8, w~9-13) with 2-4 ACTIVE ROWS, each containing a LAUNCHER — at column c, a COLOR-1 (blue) MARKER immediately followed by a COLOR CELL at (r, c+1) in a non-{0, 1, 9} color drawn from {2..8}. Some rows ALSO have a COLOR-9 (maroon) STOPPER somewhere to the right at (r, c+k) where k ≥ 3. Other rows have no stopper. Rule (EACH 1/COLOR LAUNCHER FIRES A RIGHTWARD RAY OF ITS COLOR UNTIL STOPPER OR EDGE): For EACH ACTIVE ROW r: locate the LAUNCHER — a color-1 cell at (r, c) immediately followed by a non-{0, 1, 9} color C at (r, c+1). PAINT cells (r, c+2), (r, c+3), ... with COLOR C, extending RIGHTWARD, stopping just before a COLOR-9 STOPPER or the grid right edge. Launcher and color cells stay. Net: each row's launcher paints a rightward tail in its color until a 9-stopper or the right edge.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
