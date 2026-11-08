# c6fa0b0b24da

0-bg grid (h~7-9, w~8-10) with 2-5 NON-BG CELLS all the SAME COLOR (from {1..9}), scattered at distinct positions. Two extreme cells are placed to force a bbox spanning ≥3 ROWS AND ≥3 COLS (diagonal endpoints); additional cells are scattered anywhere (may extend the bbox). Rule (REPLACE WITH SOLID RECTANGLE OF THE BBOX, FILLED IN THE INPUT COLOR): compute BBOX (min row, min col, max row, max col) of all non-0 cells. IDENTIFY the INPUT COLOR (only non-0 color in input). PRODUCE a NEW h × w OUTPUT (or input-shape) where: every cell strictly INSIDE the BBOX (including border) is painted INPUT COLOR; every cell OUTSIDE the BBOX is 0. Net: scattered same-color cells get replaced by their solid bbox rectangle in their color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
