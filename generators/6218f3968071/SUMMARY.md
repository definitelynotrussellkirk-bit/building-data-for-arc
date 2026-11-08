# 6218f3968071

11×11 0-bg grid with: (a) one color-4 rectangular frame outline with TOP row at r0, BOTTOM at r1, LEFT col at c0, RIGHT at c1; (b) 1-3 color-1 markers on the TOP edge at interior columns (replacing some 4s); (c) 1-2 color-2 markers on the LEFT edge at interior rows; (d) optionally a few decoy cells in other colors (preserved by rule). Rule: find bbox of {1, 2, 4} cells. Inside bbox, for each interior cell (r, c): if g[r][c0] == 2 (row has left-2) AND g[r0][c] == 1 (col has top-1), set to color 3. Else preserve.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
