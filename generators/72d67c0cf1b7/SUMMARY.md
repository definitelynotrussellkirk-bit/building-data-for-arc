# 72d67c0cf1b7

0-bg grid with 3-4 ISOLATED 4-conn motifs (3-5 cells each) in distinct non-zero colors at distinct positions, each surrounded by background. Rule: start from an empty grid the same size as the input. For each 4-connected non-bg object, compute its cells normalized to the bbox (0, 0) corner, rotate those normalized cells 90° CLOCKWISE inside the bbox, then paint the rotated cells back at the SAME bbox top-left in the object's color. Net effect: every object is rotated 90° CW in place (anchored at its original top-left corner).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
