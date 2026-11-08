# 5c784ca96186

0-bg grid (h×w, ~11-13 by ~12-14) with: (a) one connected color-2 (red) TEMPLATE shape, 3-4 cells, not rotationally symmetric; (b) one isolated CONTROL cell in {1, 3, 4, 6} (determines rotation amount: 1→0, 3→1, 4→2, 6→3 quarter-turns CW); (c) one isolated color-8 TARGET cell. All three components are 8-conn isolated. Rule: extract template cells; normalize. Read control color; rotate template by k=0..3 CW based on control. Stamp at target position: paint color 7 (orange) at each (target_r + offset_r, target_c + offset_c). Output: fresh canvas with only the stamped 7-pattern.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
