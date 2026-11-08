# dfa0c3bc1410

0-bg grid (h~7-9, w~8-10) with 4 BLOBS at hardcoded border positions: (a) 2-cell vertical bar TOUCHING TOP BORDER at column tc; (b) 2-cell vertical bar TOUCHING LEFT BORDER at row lr; (c) 1-cell bar TOUCHING RIGHT BORDER at row rr; (d) 2-3 cell INTERIOR BLOB growth in the middle. Each in a DISTINCT color from {2, 3, 5, 7, 9}. Rule (RECOLOR BY BORDER CONTACT): for EACH BLOB, check which BORDER its cells touch: (a) blob touching ROW 0 (top) → RECOLOR to COLOR 2 (red); (b) touching COL 0 (left) → COLOR 4 (yellow); (c) touching COL w-1 (right) → COLOR 6 (magenta); (d) fully INTERIOR (no border) → COLOR 8 (cyan). Net: blobs recolored by which border they touch.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
