# 1520a56aa617

0-bg grid (h = ch + 4, w = 2*cw + 3 with ch=4-5, cw=4-5) structured as: (a) ROW 0 = PRIORITY LEGEND with 3 DISTINCT COLORS (from {1, 2, 3, 4, 5, 6, 7, 9}, exclude 8) at cols 1, 2, 3 (sorted left = highest priority); (b) FULL-WIDTH COLOR-8 HORIZONTAL WALL at ROW 2; (c) FULL-HEIGHT COLOR-8 VERTICAL WALLS at cols 0, cw+1, w-1 (outer + 1 internal divider) starting from row 2; (d) FULL-WIDTH COLOR-8 HORIZONTAL WALL at ROW h-1. This creates an R x C chamber grid (1-2 rows by 2-3 cols). (e) Inside each chamber: 1-2 SEED CELLS in legend colors. Rule (CHAMBER FILL BY LEGEND PRIORITY): for EACH CHAMBER, identify the SEEDS present and find the one with the HIGHEST PRIORITY (= EARLIEST in the row-0 legend). FILL the entire chamber's 0-cells with that priority color. Walls + legend stay. Net: each chamber gets flooded with its highest-priority seed color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
