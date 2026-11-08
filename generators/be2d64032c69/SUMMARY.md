# be2d64032c69

0-bg grid (h, w~7-9) with: (a) ONE MULTI-COLOR SHAPE drawn from 3 hardcoded SHAPE VARIANTS (each 3-6 cells in 2-3 distinct colors from {1, 2, 4, 6}) placed in the UPPER-RIGHT quadrant; (b) ONE COLOR-5 (gray) MARKER cell at a non-adjacent position in the LOWER-LEFT quadrant. Rule (TRANSLATE SHAPE TO ALIGN CENTROID WITH 5-MARKER): identify the SHAPE (non-0 non-5 cells) and compute its CENTROID (mean of cell positions, rounded). Identify the 5-MARKER's position. COMPUTE translation delta = (marker - centroid). For EACH SHAPE cell at (r, c) with color C: ERASE the original, PAINT g[r + dr][c + dc] = C. The 5-marker is absorbed (or kept per task). Net: shape moves so its centroid lands on the gray marker.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
