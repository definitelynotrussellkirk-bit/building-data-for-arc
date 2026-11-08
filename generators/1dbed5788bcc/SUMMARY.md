# 1dbed5788bcc

Color-1 (blue) grid wall partitioning the canvas (h = nrr*(rh+1)+1, w = ncc*(rw+1)+1; nrr=2-4 rooms vertically, ncc=2-5 rooms horizontally; each room is rh×rw interior cells of 0). The blue walls form a regular ROOM GRID with carved 0-interiors. SOME WALL CELLS between adjacent rooms are DOORS (color 7) placed with probability 0.7 per adjacency. ONE ROOM contains a single color-2 (red) SEED MARKER at a random position inside. Rule: build the ROOM ADJACENCY GRAPH where two rooms are connected if a color-7 DOOR cell lies on their shared wall. Run BFS from the seed's room. For each room, FILL its 0-interior cells based on BFS distance: d=0 → 2 (red), d=1 → 3 (green), d=2 → 4 (yellow), d≥3 → 5 (gray). Walls and doors are preserved. Net: rooms are flood-filled by graph distance through doors.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
