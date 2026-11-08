# 5e87340e5e90

0-bg grid (h, w~9-16) with: (a) ONE COLOR-5 (gray) PIVOT cell at position (cr, cc) — biased to center/off_center/edge/corner; (b) 4-10 SPARSE COLORED CELLS in 2-5 DISTINCT colors from a palette (warm/cool/broad/small), placed in cell layouts (scattered/blob/diag/row/col/checker) such that every cell's 180° image around the pivot is in-bounds. Rule (ROTATE 180° AROUND GRAY PIVOT): identify the GRAY PIVOT (cr, cc). For EACH NON-BG, NON-PIVOT CELL at (r, c), COMPUTE its 180° MIRROR position (2cr - r, 2cc - c). PAINT the mirror position with the SAME COLOR. The pivot stays color 5. Originals stay. Net: each colored cell gets a same-color twin via 180° rotation around the gray pivot.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
