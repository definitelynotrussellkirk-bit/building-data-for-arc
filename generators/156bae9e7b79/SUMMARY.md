# 156bae9e7b79

Grid (h~8-14, w~9-14) with bg = color 5 (gray). ROW 0 contains a KEY ROW with sparse non-{0,5,8} cells in varied colors at random columns. A vertical color-8 (cyan) LINE in some column (line_col) extends from line_top down to line_bottom (both interior rows). Rule: detect line_col, line_top, line_bottom. Compute max_radius = (w-1)//2. For each (r, c): if r is outside [line_top, line_bottom] → keep bg(5). Else compute vis_r = min(max_radius, r - line_top). If c == line_col → 8. Else if c is in [line_col - vis_r, line_col + vis_r] (within the triangle for this row) → set to key[c] (row 0's value at column c). Else bg. Net effect: each row-0 key cell is projected DOWNWARD into an expanding triangle radiating from the cyan line.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
