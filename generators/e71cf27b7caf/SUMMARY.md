# e71cf27b7caf

0-bg grid (h~4-12, w~7-16) with 2-4 PAIR ROWS — each pair row holds EXACTLY 2 cells of COLOR 2 (red) at distinct columns (c_left, c_right), with a GAP = c_right - c_left. Gaps are assigned by one of 6 DISTRIBUTIONS (uniform / increasing / decreasing / min_at_top / min_at_bottom / alternating), starting from min_gap (2-3) and extending by up to extra (2-4). At least ONE row has the UNIQUE MINIMUM GAP (strict). Other rows (non-pair rows) have 0 cells of color 2. Pair-row positions are random (sampled without replacement). Rule (FILL CELLS BETWEEN THE TWO 2s IN EVERY ROW WHOSE GAP EQUALS THE OVERALL MINIMUM GAP): for EACH PAIR ROW r: COMPUTE its GAP = c_right - c_left. find the GLOBAL MINIMUM GAP across all pair rows. For EACH row whose gap = min_gap: FILL every cell (r, c) with c_left < c < c_right with COLOR 2 (the interior between the two 2s). The endpoint 2s stay; the other (larger-gap) pair rows keep just their endpoints unchanged. Net: the tightest pair row(s) become solid horizontal red bars; wider-gap rows stay as their two endpoints.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
