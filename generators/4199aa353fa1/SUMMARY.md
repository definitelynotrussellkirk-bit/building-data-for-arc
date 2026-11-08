# 4199aa353fa1

0-bg grid (h, w ~10-14) with: (a) one CONTROL MARKER cell in some color from {2, 3, 4, 5, 6}; (b) a BLUE(1) TEMPLATE shape of 4 cells in an asymmetric L/J pattern placed in the interior, not adjacent to the marker. Rule: detect ctrl color via (first available in 2, 3, 4, 6) → maps to rotations 0/1/2/3 CW. Take template cells (color 1) normalized; rotate ctrl times. Find anchor from grid (first color-7 cell or fallback). Output: a fresh empty grid with the rotated shape stamped at anchor position, painted color 8 (cyan).

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
