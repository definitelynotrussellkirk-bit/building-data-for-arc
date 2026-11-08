# 885554f8c5ac

0-bg grid (h~7-9, w~9-11) containing 3-5 SINGLE-CELL MARKERS, each in a DISTINCT non-zero color from {1..9}, placed at scattered random positions. Markers are individual pixels (not connected blobs) with no enforced separation beyond being at distinct cells. Rule: for EACH cell (including bg cells), COUNT the number of OTHER MARKER CELLS it can 'SEE' — a marker is visible from cell (r, c) if there's a STRAIGHT LINE (horizontal, vertical, or diagonal) connecting them with NO OTHER MARKER in between (line-of-sight along 8 cardinal/diagonal rays). RECOLOR each cell to that visibility count (e.g., 0 if it sees no marker, 1 if it sees one, etc.). Output: grid where every cell shows how many markers are visible from it. Net: input is sparse markers; output is a per-cell visibility-count heatmap.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
