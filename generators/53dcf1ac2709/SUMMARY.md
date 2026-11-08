# 53dcf1ac2709

0-bg grid (h ∈ 7-11, w ∈ 9-13 FORCED ODD so a center column exists, axis = w//2) with: (a) ONE FULL COLOR-8 (CYAN) DIVIDER COLUMN at col axis (every cell in that column painted 8); (b) COUNT ∈ 5-10 SPARSE SOURCE CELLS placed at random LEFT-HALF positions (cols 0..axis-1), each in a random color drawn from {1..9}\{0, 8}. The RIGHT HALF (cols axis+1..w-1) starts EMPTY. Rule (FOR EACH NON-BG NON-8 CELL ON THE LEFT, COPY IT TO ITS MIRROR POSITION ON THE RIGHT — MIRROR AXIS IS THE COLOR-8 DIVIDER COLUMN; ORIGINAL LEFT CELLS PRESERVED): FIND the full color-8 column → axis position c_axis. For EACH non-bg cell at (r, c) with c < c_axis and color k: COMPUTE mirror position (r, 2*c_axis - c). PAINT g[r][2*c_axis-c] = k. The left source cells and the color-8 divider stay. Net: the left-half pattern is reflected onto the right half across the cyan axis.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
