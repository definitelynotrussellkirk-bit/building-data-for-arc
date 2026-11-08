# c83b187a9e1c

FIXED 10×w grid (w ∈ [13, 15]) with: (a) COLOR-1 (blue) TEMPLATE — a fixed 5-cell shape {(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)} painted at (1, 1); (b) MATCHING CANDIDATE — same shape transformed by one of 8 DIHEDRAL TRANSFORMS (rotations + reflections), in a CANDIDATE color from {2..9} (excluding 1), placed at (1, match_left) where match_left is chosen to fit; (c) TWO DISTRACTOR shapes with DIFFERENT normalized shapes (different dihedral class), each in a DISTINCT color, placed at bottom-left and bottom-right. Rule (FIND THE CANDIDATE MATCHING THE TEMPLATE UP TO DIHEDRAL SYMMETRY, CROP, RECOLOR TO 8): identify the COLOR-1 TEMPLATE. For EACH non-1 candidate: check if its normalized shape matches any of the 8 dihedral variants of the template's normalized shape. Find the UNIQUE match. CROP it to its BBOX. RECOLOR ALL its cells to COLOR 8 (cyan). Output is the cropped matching candidate in cyan. Flag: INTRINSIC-LOW — fixed template × 8 variants → 4 distinct cropped shapes.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
