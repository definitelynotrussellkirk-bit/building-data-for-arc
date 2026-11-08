# 12a886996b14

0-bg grid (h ∈ 6-10, w ∈ 10-14) with: (a) ONE COLOR-2 (RED) MARKER CELL and ONE COLOR-3 (GREEN) MARKER CELL placed at positions related by a small VECTOR (dr ∈ -2..2, dc ∈ 0..4, non-zero); (b) 1-3 COLOR-4 (YELLOW) CELLS placed at random free positions where the translated position (r+dr, c+dc) is in-bounds. Rule (COMPUTE THE DELTA VECTOR FROM RED-MARKER'S BBOX TOP-LEFT TO GREEN-MARKER'S BBOX TOP-LEFT; FOR EACH YELLOW CELL AT (R, C), PAINT COLOR 4 AT (R+DELTA.R, C+DELTA.C) ON A FRESH EMPTY GRID): LOCATE the RED-2 and GREEN-3 BBOXES. COMPUTE delta = (g_bbox.r1 - r_bbox.r1, g_bbox.c1 - r_bbox.c1). PRODUCE a fresh same-size grid of 0s. For EACH yellow-4 cell at (r, c): PAINT g_out[r+delta.r][c+delta.c] = 4. The red and green markers are NOT preserved. Net: yellow shape is translated by the red→green vector to its new position on a fresh canvas.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
