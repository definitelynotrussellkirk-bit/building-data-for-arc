# dfa5c1702b4c

Two to seven distinct-color solid rectangles, separated by a one-cell moat on
background 0. In bounding-box top/left order, return the pairwise inclusive
projection matrix: both axes = 3, rows only = 1, columns only = 2, neither = 0.

Version 3.0.1 honors exact grid height, grid width and distinct-color/object
count. Its period-2 default schedule alternates teaching inputs with varied
rectangle layouts. Teaching inputs distinguish one-cell overlaps, equal-top
left ordering, and bottom/center ordering. Canonical dimension/count profiles
have support in every band. Reference rule `5264524f1c03` is unchanged.

See `notes.md`, focused tests, and `workspace/README.md` for evidence, reusable
diagnostics, and the finite scope of the eight-rival lesson checks.
