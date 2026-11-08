# b34d330a5426

Grid (h~6-10, w~7-12) with bg = 7 (orange). At the BOTTOM there are exactly TWO vertical BARS: one in col col_8 of color 8 (cyan), one in col col_2 of color 2 (red). Each bar's height = how many cells from the bottom up are non-7 in that column. Bars have DIFFERENT heights. (col_2 + 2) must be in-bounds. Rule: scan bottom row to find bar columns. Compute height_8 and height_2 by counting non-7 cells in each bar's column. gray_h = |height_8 - height_2|. new_col = (rightmost bar col) + 2. Paint a color-5 (gray) bar in column new_col, occupying the bottom gray_h rows. All other cells preserved.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
