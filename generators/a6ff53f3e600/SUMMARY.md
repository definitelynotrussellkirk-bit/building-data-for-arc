# a6ff53f3e600

FIXED 5×5 grid with: (a) FOUR COMMAND CELLS — at fixed positions (2, 0) = rc1 (row command 1), (4, 0) = rc2 (row command 2), (0, 1) = cc1 (col command 1), (0, 3) = cc2 (col command 2), each ∈ {1, 2, 3}; (b) 3×3 MOTIF — at subgrid (2, 1)..(4, 3) filled with COLOR 4 in a specific shape pattern: cells (3, 2), (3, 3), (4, 1), (4, 2), (4, 3) all = 4 (an inverted L shape). Rule (2×2 META-TILE TRANSFORM PER (ROW CMD, COL CMD) PAIR): output is a 2×2 GRID of TILES, each a COPY of the 3×3 motif transformed by the (row_cmd, col_cmd) pair at that tile position: tile (0, 0) uses (rc1, cc1); tile (0, 1) uses (rc1, cc2); tile (1, 0) uses (rc2, cc1); tile (1, 1) uses (rc2, cc2). Each cmd ∈ {1, 2, 3} applies a specific transform (identity, horizontal-flip, vertical-flip per puzzle convention). Net: 4 transformed copies of the motif tiled together by command-pair lookup.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
