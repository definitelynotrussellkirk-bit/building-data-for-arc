# 3dc5b297cfa2

One 4-connected two-color shape appears on a unique nonzero modal background. Swap the two shape colors. Cells in the top half of the shape bounding box, including the floor midpoint row, move horizontally while bottom-half cells stay in place. The selected canonical rule moves the top half right. Its shift is the full shape-bbox width except when black (`0`) is a shape color, where it is the horizontal span of the nonblack shape cells.

Generator v3.1.1 advertises six exact axes: grid height 12–20, grid width 16–24, bbox height 4–8, bbox width 3–7, background color 1–9, and black/nonblack shape branch. The six-slot default schedule is `black, black, nonblack, black, black, nonblack`, using both broad and linked canonical profiles. A production lesson has two ordered demonstrations and one query; every three-pair cyclic window retains black-branch evidence after any single query holdout.

A separate non-production prototype under `workspace/parametric/` varies `moving_half = top|bottom` and `direction = right|left` once per episode. The canonical/default setting is `top + right` and materializes the selected canonical Racket program byte-for-byte.

Kind: `per_puzzle`. Imported/reviewed version: `3.1.1`. Canonical rule hash: `69b3b2d19383`.
