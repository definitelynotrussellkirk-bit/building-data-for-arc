# 3fcea70c3acf

0-bg grid (h~8-11, w~12-16) with 2-3 CONNECTED NON-BG OBJECTS, each a DISTINCT SHAPE drawn from a 2-7-cell shape bank (sizes 2, 3, 4, 5, 6, 7) in DISTINCT COLORS, placed at non-overlapping non-touching positions (1-cell padding via bbox-overlap check). Each object has a UNIQUE cell-count so the size-sort is unambiguous. Rule (SORT OBJECTS BY SIZE DESC, PASTE BBOX CROPS SIDE-BY-SIDE): extract every 4-CONNECTED NON-0 COMPONENT. For each, compute its BBOX CROP (subgrid containing the shape, padded to bbox). SORT the crops by CELL COUNT DESCENDING (tiebreakers: top-row, left-col, color). PASTE the sorted crops HORIZONTALLY with 1-column GAP of 0 background between adjacent crops. Output is a fresh grid sized to fit the row of crops. Net: objects lined up biggest-first left-to-right with a gap between each.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
