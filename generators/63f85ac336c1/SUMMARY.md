# 63f85ac336c1

0-bg grid (h~9-12, w~11-14) with 2-4 PARTIAL-BBOX COMPONENTS all in COLOR 4 — each shape drawn from _PARTIALS bank (L-trominoes / 5-cell U / 6-cell U-with-hole) chosen so each component's CELL COUNT < bbox area (non-rectangular). Components are placed at non-overlapping positions with 1-cell padding (used cell set tracked, including bbox cells to prevent bbox overlap). All components share color 4. Rule (REPLACE EACH 4-COMPONENT WITH A SOLID FILLED RECTANGLE COVERING ITS BBOX, IN COLOR 4): for EACH 4-CONNECTED color-4 COMPONENT: COMPUTE its bbox (r1, c1, r2, c2). PAINT every cell in the bbox (rows r1..r2 × cols c1..c2) with COLOR 4. Cells outside any component's bbox stay bg-0. The original cells are absorbed into the filled bbox. Net: each irregular color-4 component inflates into a solid color-4 rectangle of the same bbox.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
