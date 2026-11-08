# 2365d033c2b8

0-bg grid (h~7-9, w~9-11) with 2 DISTINCT NON-{0, 9} COLORS, each appearing as EXACTLY 2 CELLS at AXIS-ALIGNED positions (same ROW or same COLUMN) at EVEN DISTANCE ≥ 2 (so the integer midpoint is well-defined). Pair cells and midpoints don't overlap between pairs. Other cells are 0. Rule (PAINT MIDPOINT OF EACH EVEN-DISTANCE SAME-COLOR PAIR WITH MAROON 9): for EACH COLOR C with EXACTLY 2 CELLS at (r1, c1) and (r2, c2) sharing row OR column at EVEN distance: COMPUTE MIDPOINT ((r1+r2)//2, (c1+c2)//2). PAINT the midpoint cell with COLOR 9 (maroon). Endpoints stay at C. Colors with !=2 cells or odd-distance pairs are skipped. Net: each axis-aligned same-color pair gets a maroon dot between them at the midpoint.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
