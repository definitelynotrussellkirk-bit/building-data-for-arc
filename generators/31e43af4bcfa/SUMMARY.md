# 31e43af4bcfa

Row 0 is a left-aligned palette of K distinct colors. Rows 1+ contain K separate 4-connected color-1 objects. Sort the objects by (cell count ascending, top row ascending, left column ascending), recolor them with the palette in that order, crop each object to its bounding box, and pack the crops left-to-right with one zero column between adjacent pieces. Equal-size objects are intentional: top row, then left column, resolves ties.

The teaching schedule uses five demonstrations. Its distinct-rank example places
a square of area 4 before a diagonally touching L of area 3. Their equal
perimeters and bounding-box areas distinguish actual cell-count ranking, while
the diagonal contact distinguishes 4-connectivity from 8-connectivity. The other
two scheduled examples teach row and column tie breaks. Six consecutive pairs
contain two examples of each profile, supporting every single-query holdout
against the seven declared rivals.

Kind: `per_puzzle`. Selected version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
