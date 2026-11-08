# b20d975c39c8

0-bg grid (h~11-13, w~13-16) with 3 ISOLATED 4-CONNECTED COMPONENTS in distinct colors from {1..9}, each with a DISTINCT ENCLOSED-HOLE COUNT: (a) SOLID BLOCK — 2×2 / 2×3 / 3×2 with 0 holes; (b) HOLLOW RING — 3×3 / 3×4 / 4×3 outline with 1 enclosed hole; (c) DOUBLE-HOLED RING — 3×5 / 3×6 / 5×3 with an extra divider line creating 2 enclosed holes. Components are placed at non-touching positions. Rule (SORT COMPONENTS BY (HOLE-COUNT DESC, AREA DESC, COLOR ASC), PACK BBOX CROPS HORIZONTALLY): for each 4-CONNECTED COMPONENT: crop to BBOX, compute HOLE-COUNT (# enclosed zero regions inside the crop). SORT by (hole_count DESC, area DESC, color ASC). PACK the crops LEFT-TO-RIGHT with 1-column BLANK GAP between adjacent crops. Output dimensions = max(crop rows) × (sum(crop cols) + gaps). Net: components stacked left-to-right by complexity (holes first, then area).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
