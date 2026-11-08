# cb338b1a9994

0-bg grid (h ∈ 7-11, w ∈ 8-12, by difficulty) with: (a) ONE COLOR-1 MARKER at (r1, c1) drawn from r1 ∈ 0-1, c1 ∈ 0-2 (top-left region); (b) ONE COLOR-2 MARKER at (r2, c2) drawn from r2 ∈ 2-3, c2 ∈ 3-4 (offset toward bottom-right) — these define a translation vector (dr, dc) = (r2-r1, c2-c1); (c) ONE CONNECTED MOTIF — a 3-5 cell motif built via _build_motif random walk, painted in a non-{0,1,2} color drawn from {3..9}, placed in the LOWER HALF (rows ≥ h//2). Rule (COMPUTE TRANSLATION VECTOR FROM COLOR-1 TO COLOR-2 MARKER; FOR EACH NON-{0,1,2} CELL, PAINT THE SAME COLOR AT (R + DR, C + DC); ORIGINAL MOTIF AND MARKERS PRESERVED): LOCATE markers; COMPUTE v = marker2 - marker1. For EACH non-{0,1,2} cell at (r, c) with color k: PAINT g[r+v.r][c+v.c] = k (if in-bounds). Net: motif is duplicated by the marker vector to a new position; original kept.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
