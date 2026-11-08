# ef82795e0087

0-bg grid (h, w~8-11) with EXACTLY ONE COLOR-8 (cyan) ANCHOR cell at interior position (ar, ac) (not at grid edge, so reflections fit). Plus 2-7 non-{0, 8} CELLS in various colors from {1, 2, 3, 4, 5, 6, 7, 9} placed at scattered positions such that their point-reflection through the anchor lands IN-BOUNDS at currently empty cells. Rule: TREAT the COLOR-8 ANCHOR as the FIXED REFLECTION CENTER. For every non-{0, 8} cell at (r, c) with value v, COMPUTE its POINT-REFLECTION (2*ar - r, 2*ac - c). If that reflected position is in-bounds, PAINT it with the SAME COLOR v. ORIGINAL CELLS STAY. The anchor stays color 8. Net: every colored cell gets a same-color twin point-mirrored across the cyan anchor; output is input + all reflected copies.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
