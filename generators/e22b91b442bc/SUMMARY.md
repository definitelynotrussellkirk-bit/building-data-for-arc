# e22b91b442bc

0-bg grid (h~11-14, w~14-18) with 3 ISOLATED COMPONENTS each in a DISTINCT color from {1..9}\{0}, each with a DISTINCT HOLE COUNT from {0, 1, 2}: (a) SOLID rect (0 holes); (b) HOLLOW RING (1 hole); (c) DOUBLE-RING with 2 holes. Components placed non-touching with 1-cell padding. Rule (SORT BY (HOLE_COUNT ASC, AREA ASC, COLOR ASC), PACK CROPS LEFT-TO-RIGHT WITH 1-COL GAPS): identify all 4-conn COMPONENTS. For EACH: CROP to BBOX, COUNT enclosed-zero holes (regions of 0 inside the bbox that don't touch the rim). SORT by (hole_count asc, area asc, color asc). HCONCAT the cropped components left-to-right with 1-COL GAPS in sorted order. Net: components rearranged by hole complexity, packed horizontally.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
