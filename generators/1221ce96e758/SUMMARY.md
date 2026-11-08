# 1221ce96e758

0-bg grid (h~7-12, w~7-12) with 2-5 ISOLATED YELLOW L-TRIOMINOES placed at GRID-ALIGNED ANCHORS on a 3-step grid (anchors at rows 0,3,6,9,... × cols 0,3,6,9,...). Each L-triomino is a 2×2 window with EXACTLY 3 of the 4 cells painted YELLOW (color 4) and the FOURTH (missing) CORNER left as 0. Which of the 4 corners is missing is chosen uniformly at random per shape (encoding one of 4 ORIENTATIONS). Triominoes are placed at non-touching positions via the 3-step grid alignment. Rule (PAINT THE MISSING CORNER OF EACH L-TRIOMINO WITH AN ORIENTATION-CODED COLOR): for EACH yellow L-triomino (3 yellow cells in a 2×2 window with one 0 corner): IDENTIFY which of the 4 corners is missing (top-left, top-right, bottom-left, bottom-right). LOOK UP the missing-corner color from a fixed mapping that depends on orientation (e.g., TL→C1, TR→C2, BL→C3, BR→C4 per demos). PAINT the missing-corner 0 cell with that color. Yellow cells stay yellow. Net: each yellow L is closed into a 2×2 block whose new corner has an orientation-coded color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
