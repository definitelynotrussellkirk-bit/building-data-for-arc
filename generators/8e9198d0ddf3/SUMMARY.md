# 8e9198d0ddf3

0-bg grid (h~7-12, w~8-14) with: (a) ONE COLOR-2 (red) MARKER at (r, c1) and ONE COLOR-3 (green) MARKER at (r, c2) — same row r (random interior), with c2 ≥ c1 + 3; (b) SCATTERED COLOR-5 (gray) WALL CELLS at ~18% density in OTHER rows (NOT row r), placed at random rows for each column. The direct horizontal route between markers is unblocked. Rule (BFS SHORTEST PATH FROM RED TO GREEN, PAINT CYAN): from the COLOR-2 red marker, BFS through all 4-conn 0-cells, AVOIDING color-5 walls and the markers themselves, to find the SHORTEST PATH to the COLOR-3 green marker. PAINT every cell on that path with COLOR 8 (cyan). Markers and walls stay. Net: cyan shortest-path connects red→green across the grid.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
