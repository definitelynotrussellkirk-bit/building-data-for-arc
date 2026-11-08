# fd2ddef14b82

0-bg grid (h~8-10, w~10-12) structured as a small dungeon: (a) ONE COLOR-2 (red) START cell at random position; (b) ONE COLOR-3 (green) GOAL cell at another position with Manhattan distance ≥4 from start; (c) 0-4 COLOR-5 (gray) WALL cells at random empty positions; (d) 0-1 COLOR-6 (magenta) KEY cell; (e) 0-2 COLOR-7 (orange) DOOR cells. Rule (BFS PATH WITH KEY/DOOR): find the SHORTEST PATH from start to goal using BFS where WALLS (5) block movement; DOORS (7) block UNLESS the KEY (6) has been picked up earlier on the path. PAINT every cell on the shortest path with COLOR 4 (yellow). If unreachable, output = input. Start/goal/key/door/walls stay. Net: BFS shortest path → yellow trace, with key→door unlock logic.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
