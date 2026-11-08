# 3e18c05a8b57

0-bg grid (h ∈ 8-11, w ∈ 10-13) with: (a) ONE 180°-SYMMETRIC COMPONENT — drawn from _180_SYM bank (4 four-connected variants: 2×2 square, plus, H/7-cell, S-tetromino), painted in palette[0] at a random non-overlapping position via _free_box (1-cell padding); (b) 1-2 ASYMMETRIC COMPONENTS — drawn from _ASYM bank (5 variants: L-tromino, S-tromino, P-tetromino, L-tetromino, S-tet), each in a DISTINCT non-symmetric color drawn from palette[1:]. All colors distinct, drawn from {1,2,3,4,6,7,8,9}. Rule (FIND THE UNIQUE 180°-SYMMETRIC COMPONENT, CROP TO ITS BBOX, OUTPUT): EXTRACT every 4-connected non-bg COMPONENT (single-color). For EACH component: COMPUTE its NORMALIZED BINARY SHAPE; CHECK if shape == its 180° ROTATION. SELECT the unique component where shape is 180°-symmetric. CROP it to its bounding box. OUTPUT the cropped grid (preserving the component's color, 0 elsewhere in bbox). Net: the symmetric shape is extracted; asymmetric distractors discarded. Flagged intrinsic-low (uniq_out=28): small bank × few colors bounds outputs.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
