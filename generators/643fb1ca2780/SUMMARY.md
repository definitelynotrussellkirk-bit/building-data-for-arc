# 643fb1ca2780

Fixed 11×14 grid, 0-bg, with: (a) ONE color-1 (blue) HOLLOW FRAME (4×4 outline) at (1, 1) supplying the HOLE-COUNT spec (one interior hole); (b) ONE color-2 (red) DOUBLY-SYMMETRIC shape (plus-shape, both H and V symmetric) at (1, 8) supplying the SYMMETRY-CLASS spec; (c) ONE other-color TARGET object — a hollow frame with 1 hole AND matching symmetry class — at (6, 6); (d) ONE DECOY object with NEITHER one hole NOR matching symmetry at (6, 1). Rule: read the blue object's HOLE COUNT (= 1) and the red object's SYMMETRY CLASS (= both H+V). Find the non-blue/non-red object matching BOTH features. CROP that target to its bbox and RECOLOR to 8 (cyan). Net: anchors specify hole-count + symmetry; output is the matching candidate recolored to cyan.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
