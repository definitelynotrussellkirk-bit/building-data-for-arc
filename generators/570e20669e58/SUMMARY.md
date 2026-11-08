# 570e20669e58

0-bg grid (h ∈ 8-13, w ∈ 9-13, by difficulty) with: N_COLORS ∈ 3-4 DISTINCT non-bg colors drawn from {1..9}, each appearing EXACTLY TWICE as ISOLATED single cells (no two non-bg cells within Chebyshev-distance 1, enforced via _too_close). Generation retries up to 40 outer attempts until all pairs placed cleanly. Rule (FOR EACH COLOR-PAIR, DRAW BOTH POSSIBLE 'ELBOW' PATHS BETWEEN ITS TWO ENDPOINTS (GO HORIZONTAL-THEN-VERTICAL OR VERTICAL-THEN-HORIZONTAL); PER CELL, COUNT HOW MANY ELBOW PATHS PASS THROUGH; OUTPUT A FRESH SAME-SIZE GRID WHERE EACH CELL'S VALUE ENCODES THE OVERLAY COUNT: 1→COLOR 2, 2→COLOR 3, 3+→COLOR 4, ELSE 0): For EACH color pair (p1, p2): GENERATE the 2 elbow paths between p1 and p2 (one with horizontal-then-vertical, one with vertical-then-horizontal). For EACH cell along these paths: INCREMENT its overlay count. PRODUCE output: count=0→0, count=1→2 (red), count=2→3 (green), count≥3→4 (yellow). Net: dense intersections appear in brighter colors; sparse paths in red.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
