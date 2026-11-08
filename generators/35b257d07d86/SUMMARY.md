# 35b257d07d86

0-bg grid (h~8-14, w~8-14) with: (a) A 2-COLUMN × kh-TALL (kh ∈ [3, 5]) KEY TABLE — a solid rectangle at (kr0, kc0)..(kr0+kh, kc0+1) where each row r of the key holds a (LEFT_COLOR, RIGHT_COLOR) PAIR (distinct colors from a palette, encoding the mapping LEFT → RIGHT); (b) OPTIONAL VERTICAL SEPARATOR LINE at col w//2 in COLOR 2 (sometimes present, sometimes not); (c) SPARSE TARGET CELLS outside the key bbox in values drawn from the key's LEFT colors (so they trigger substitution). Rule (APPLY KEY-TABLE SUBSTITUTION TO ALL CELLS OUTSIDE THE KEY BBOX): identify the KEY TABLE (2-column × kh-tall solid multicolor component). PARSE each key row as a MAPPING LEFT_COLOR → RIGHT_COLOR. For EACH CELL OUTSIDE the key bbox: if its color matches any key row's LEFT color, RECOLOR to that row's RIGHT color. Else, keep. Key table stays intact. Net: target cells get substituted color-by-color according to the table's lookup.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
