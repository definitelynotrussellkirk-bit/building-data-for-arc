# 10b0b0da4c28

Period-4 8-LATTICE background: at each block offset (rows/cols 1..3 of every 4-cell block) a 3x3 hollow 8-box, with 0 gutters on the lines (r%4==0 / c%4==0) and a 0 center (r%4==2,c%4==2). Scattered markers in 2-3 colors (not 0/8) sit on the 0 cells. Rule: snap each color's markers to the nearest 4-lattice lines, form a bounding rect, paint its border + lattice-center dots (r%4==2,c%4==2) in that color (only over 0-cells; the 8-boxes are preserved); markers are kept. Grid size/colors/positions vary.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
