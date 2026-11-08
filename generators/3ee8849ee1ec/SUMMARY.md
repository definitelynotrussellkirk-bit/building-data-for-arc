# 3ee8849ee1ec

0-bg grid (h, w ~7-10) with up to 4 color-4 (yellow) cells marking the corners of a rectangle (rows r1, r2 with r2 ≥ r1 + 3; cols c1, c2 with c2 ≥ c1 + 3). All 4 corners are at (r1, c1), (r1, c2), (r2, c1), (r2, c2). Sometimes an extra midpoint cell is also painted. Rule: detect the 4 rectangle corners. ROW CLOSURE: paint every cell in rows r1 and r2 between columns c1..c2 with color 4 (top and bottom rails). COL CLOSURE: paint every cell in cols c1 and c2 between rows r1..r2 with color 4 (left and right rails). Net: the 4 corners get connected into a hollow rectangle outline in color 4.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
