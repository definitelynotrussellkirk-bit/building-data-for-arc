# 109a03554ed3

0-bg grid (h~10-15, w~12-17) with: (a) ONE RED (COLOR-2) SHAPE of 2-4 cells with ONE MAROON (COLOR-9) ANCHOR cell embedded; (b) ONE BLUE (COLOR-1) SHAPE of 2-4 cells with its OWN MAROON ANCHOR; (c) ONE CYAN (COLOR-8) TARGET cell at a clear non-adjacent position. All shapes placed with 1-cell padding. Rule (XOR OF RED AND BLUE SHAPES, STAMPED AT CYAN ANCHOR, COLOR 3): identify the RED SHAPE and its 9-anchor; the BLUE SHAPE and its 9-anchor. NORMALIZE each shape by its 9-anchor (offsets relative to anchor). COMPUTE the SYMMETRIC DIFFERENCE (XOR) of the offset sets — cells in red OR blue but NOT BOTH. STAMP the XOR offsets centered at the CYAN anchor in COLOR-3 (green). Source shapes and cyan stay or are task-specific. Net: asymmetric XOR of two anchored shapes paints in green at cyan target.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
