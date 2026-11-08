# 7fdbaba4995e

0-bg grid (h, w~8-14) with: (a) ONE COLOR-8 (cyan) cell at (cy_r, cy_c); (b) ONE COLOR-2 (red) cell at (re_r, re_c). Two endpoints at STRICTLY DIFFERENT rows AND DIFFERENT columns. Positions biased by quadrant (opposite_corner / same_corner / spread / edge) and distance (near / medium / far / diagonal / knight). No other non-bg cells. Rule (DRAW L-PATH WITH CORNER AT (re_r, cy_c)): draw an L-SHAPED PATH of COLOR 4 (yellow) connecting cyan to red. Specifically: VERTICAL SEGMENT from (cy_r ± 1, cy_c) to (re_r, cy_c) (inclusive of the corner); HORIZONTAL SEGMENT from (re_r, cy_c ± 1) to (re_r, re_c ∓ 1). Cyan and red endpoints stay. Net: L-shaped yellow path with corner at (re_r, cy_c) connects cyan→red.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
