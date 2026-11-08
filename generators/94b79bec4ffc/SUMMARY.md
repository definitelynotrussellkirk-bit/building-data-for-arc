# 94b79bec4ffc

0-bg grid (h ∈ 6-9, w ∈ 9-13) with: ROW_COUNT ∈ 3-5 ACTIVE ROWS, each with: (a) ONE ROW MARKER at EITHER LEFT EDGE (col 0, color 1) OR RIGHT EDGE (col w-1, color 2) — chosen randomly per row; (b) ONE COLORED SEGMENT of length 2-min(5, w-3) painted in a distinct color drawn from {3..9}\{1, 2}, placed at a random middle column position (NOT at the same edge as the marker). Inactive rows stay all-0. Rule (FOR EACH MARKED ROW, DOCK ITS COLORED SEGMENT AGAINST THE MARKER'S EDGE — MARKER=1 (LEFT) → SEGMENT MOVES LEFT TO TOUCH COL 0 (JUST AFTER MARKER); MARKER=2 (RIGHT) → SEGMENT MOVES RIGHT TO TOUCH COL W-1): For EACH row with a marker: CLEAR the segment's current cells to 0. REPLACE with the segment STARTING at col 1 (if marker is at left/color 1) OR ENDING at col w-2 (if marker is at right/color 2). The marker stays at its edge. Net: each row's segment is pulled toward the row's edge-marker, docking against it.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
