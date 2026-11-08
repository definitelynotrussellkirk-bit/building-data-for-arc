# 81e185a45bfa

0-bg grid (h~7-10, w~8-12) with 3-5 PAIRS of SAME-COLOR ENDPOINTS — each pair has two cells separated by EXACTLY ONE BG cell axis-aligned: HORIZONTAL (r, c) and (r, c+2) with (r, c+1) = 0, OR VERTICAL (r, c) and (r+2, c) with (r+1, c) = 0. Pairs use DISTINCT colors and are placed at NON-TOUCHING positions (8-conn padding). Rule (BRIDGE EACH DISTANCE-2 SAME-COLOR PAIR'S MIDDLE CELL): For EACH PAIR of cells with SAME COLOR C at axis-aligned distance 2 with a single BG-0 cell between them: PAINT the middle cell with color C. Endpoints stay. Net: each bridge fills its midpoint gap with the matching color.

Kind: `per_puzzle`. Imported version: `2.0.0-selfcheck`.
Approval is derived by the catalog from current code and retained evidence.
