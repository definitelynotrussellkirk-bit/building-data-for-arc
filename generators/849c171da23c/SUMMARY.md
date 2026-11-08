# 849c171da23c

0-bg grid (h~8-14, w~7-14) with ONE VERTICAL BAR of COLOR 5 starting at row 0 — a single contiguous column at col c0 with length L ∈ [3, 7] (bar covers rows 0..L-1 at column c0). Bar column has edge_clearance ≥2 from both left and right borders. Position bias selects center / left / right / spread. Rule (STAIR-STEP FILL FROM THE BAR — 8s LEFT, 6s RIGHT): the 5-bar has length L. For each row r in 0..L-1: fill cells (r, c0-1), (r, c0-2), ... out to (r, c0-(L-r)) with COLOR 8 (a left shrinking stair). And fill cells (r, c0+1), (r, c0+2), ..., out to (r, c0+(L-r)) with COLOR 6 (right shrinking stair). The 5-bar stays. Net: each row of the bar emits a shrinking 8-pyramid to the left and 6-pyramid to the right.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
