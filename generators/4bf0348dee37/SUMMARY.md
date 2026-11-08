# 4bf0348dee37

0-bg grid (h, w~8-10) with: (a) TWO ENDPOINT CELLS in COLOR 2 at distinct interior positions with different rows AND different cols; (b) ONE ELBOW CELL in COLOR 3 at a distinct interior position with row matching one endpoint and col matching the other endpoint; (c) TWO COLOR-5 (gray) OBSTACLE CELLS at (0, w-2) and (0, w-1) (top-right corner). Rule (DRAW L-SHAPED PATH IN COLOR 2 CONNECTING ENDPOINTS VIA ELBOW, BLOCKED BY 5-WALLS): identify the 2 COLOR-2 ENDPOINTS A and B and the 1 COLOR-3 ELBOW E. The ELBOW is at (A.row, B.col) or (B.row, A.col). DRAW an L-PATH: from A → E → B via straight horizontal then vertical (or vice versa) segments, PAINTING each intermediate cell and the elbow with COLOR 2 (overwriting the elbow's 3). The path is BLOCKED by color-5 cells (skip those). Endpoints stay. Net: the L-path connects the 2 endpoints through the elbow in color 2.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
