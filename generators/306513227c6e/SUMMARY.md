# 306513227c6e

0-bg grid (h, w ~ 8-12) with: (a) COLOR-2 MARKER at (base_r, base_c) and COLOR-3 MARKER at (base_r+dr, base_c+dc) where (dr, dc) is drawn from {(1, 2), (2, 1), (-1, 2), (2, -1)} — the marker pair defines a non-zero VECTOR (dr, dc); (b) 4 MOTIF CELLS painted in COLOR 4 at random interior positions chosen so each motif's shifted position (r+dr, c+dc) is in-bounds and not overlapping any marker. Rule (THE 2/3 MARKER PAIR DEFINES A VECTOR — COLOR-4 CELLS ARE KEPT AND COPIED BY THAT VECTOR AS COLOR 8): identify the COLOR-2 MARKER and COLOR-3 MARKER; COMPUTE the VECTOR (dr, dc) = (3-marker's position) - (2-marker's position). For EACH COLOR-4 CELL at (r, c): KEEP it as 4 in the output; PAINT the cell at (r+dr, c+dc) with COLOR 8 (cyan). The original 2 and 3 markers stay. Net: each color-4 cell duplicates to its vector-shifted position in color 8.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
