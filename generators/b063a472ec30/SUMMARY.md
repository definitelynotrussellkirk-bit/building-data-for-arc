# b063a472ec30

0-bg grid (h~8-14, w~14-22) with 2-4 HORIZONTAL SOLID BARS, each 3 rows tall and 5-16 cols wide, painted in distinct non-bg colors. Bars are vertically separated (≥1 row gap between bars). Each bar's MIDDLE ROW has cells equal to the cells DIRECTLY ABOVE and DIRECTLY BELOW (since the whole bar is solid). Rule: scan every cell at (r, c). If the cell ABOVE and the cell BELOW share the SAME non-zero value v (i.e., the cell is in the middle row of a 3-tall bar), find the LEFTMOST such matching cell in this row-group and HOLLOW OUT alternate cells starting from there: every OTHER middle-row cell (parity from leftmost) becomes 0. The top and bottom rows of each bar stay solid. Net: each solid 3-tall bar gets its middle row turned into a dashed pattern of alternating filled/empty cells.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
