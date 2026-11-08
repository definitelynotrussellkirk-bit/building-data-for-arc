# 3dbd1a94c4d7

13×13 0-bg grid with 1-3 PLUSES, each at fixed centers {(3,3), (9,5), (5,10)}. Each plus has a non-{0,3} CENTER cell and 4 cardinal ARMS in color 3 (green). Pluses use distinct center colors. Rule: detect pluses by their 4-green-arm pattern. For each empty bg cell (r, c), look for a plus whose center is on the same COLUMN c and whose column-extent (cells in col c reachable from center without hitting another plus's arm) includes r. If yes → paint with that plus's center color. Else check row-extent on the same row. Net: each plus's center color shoots row and column rays that stop at other pluses' arms; column projections take priority where both row and column rays cover a cell.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
