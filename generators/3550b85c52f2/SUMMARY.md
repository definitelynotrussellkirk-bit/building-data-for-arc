# 3550b85c52f2

0-bg grid (h~7-10, w~8-12) with: (a) cells (0,0) and (0,1) = TWO TRANSFORM COMMAND values in {1..5}; (b) one MOTIF (3-5 connected cells in 2-3 colors) placed in the interior, away from (0,0)/(0,1). Rule: read cmd1 = grid[0][0], cmd2 = grid[0][1]. Clear those two cells. Crop the rest to its non-zero bbox (the motif). Apply cmd1 then cmd2 in order, each chosen by code: 1 = rot-CW, 2 = 180°, 3 = flip-LR, 4 = flip-UD, 5+ = transpose. Output: motif after both transforms applied.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
