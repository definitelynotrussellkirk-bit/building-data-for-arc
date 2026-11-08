# 98066c7e6fc5

0-bg grid (h~9-13, w~11-16) with: (a) ONE DIRECTION-CODED SOURCE at (h-2, 1) — a single cell with COLOR 2 (direction index in [1..4]: 1=right, 2=down, 3=left, 4=up per puzzle); (b) ONE SLASH MIRROR (COLOR 6) at (h-2, mirror_c) with mirror_c ∈ [4, w-4]; (c) ONE WALL (COLOR 5) at (2, mirror_c) blocking upward travel; (d) OPTIONALLY ONE BACKSLASH MIRROR (COLOR 7) at (h-2-3, mirror_c+2). Rule (TRACE CYAN BEAM FROM SOURCE THROUGH MIRRORS UNTIL EDGE/WALL): the source's value encodes a direction. Cast a beam from source's position in that direction. The beam traverses 0-cells (painting them COLOR 8 cyan). When it hits a SLASH MIRROR (6), the beam reflects right-angle per the slash convention (e.g., right→up, down→left). When it hits a BACKSLASH MIRROR (7), it reflects the other way (e.g., right→down, up→left). GRAY WALL (5) STOPS the beam. Edges of the grid also stop it. Source/mirrors/walls stay. Net: a cyan-painted trajectory traces through the optical system.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
