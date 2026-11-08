# 21c9650143ce

0-bg grid (h~7-10, w~8-12) structured as: (a) ROW 0 = SOURCE LEGEND with 2-4 source colors at sorted random columns; (b) ROW 1 = TARGET LEGEND with the matching destination colors at the same columns; (c) ROWS 2..h-1 = BODY with ~38% density of cells in SOURCE colors only (scattered). At least one body cell is guaranteed at (2, 0) in the first source color. Rule (LEGEND-DIRECTED RECOLOR): build a MAP {src → dst} from rows 0 and 1 (for each non-zero col c, map[row0[c]] = row1[c]). For EACH BODY CELL (rows 2..h-1) with a source-color value v, RECOLOR it to map[v]. Cells in non-mapped colors or 0 stay. Net: top-two-row legend translates body source colors to their dest colors.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
