# 00dc84bcd438

0-bg grid with N (1-4) multicolor 2×2 shapes, each composed of 3 body-color cells and 1 special-color cell at one of the 2×2 corners (TL/TR/BL/BR). Each shape's special color is unique. For each shape, a matching singleton in the special color sits elsewhere on the grid. Rule: for each shape, identify which corner is the special. Compute the diagonally OPPOSITE corner and use it as the shape's 'anchor'. Move the whole shape so this anchor lands at the singleton marker. The shape is erased at its original position and redrawn at the new position. Markers and bg cells are unaffected except where the moved shape now lands.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
