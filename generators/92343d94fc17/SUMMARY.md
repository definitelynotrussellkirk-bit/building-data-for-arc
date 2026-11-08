# 92343d94fc17

0-bg grid (h~6-10, w~7-11) with: (a) ONE FULL-HEIGHT COLOR-8 (cyan) DIVIDER COLUMN at col `guide_col` (random 2..(w-1)//2 — left of center so the mirror fits on the right side); (b) 4-(guide_col*h/2) non-{0, 8} CONTENT CELLS on the LEFT SIDE ONLY (cols 0..guide_col-1) at random positions in ONE random color from {1..9} minus {0, 8}. Right side starts all 0. Rule (REFLECT LEFT ACROSS 8-DIVIDER): identify the cyan VERTICAL DIVIDER at col `guide`. For EACH non-bg non-8 CELL at (r, c) with c < guide, PAINT the MIRROR position (r, 2*guide - c) on the right with the SAME COLOR. Divider stays. Net: left content reflected across cyan column to right side.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
