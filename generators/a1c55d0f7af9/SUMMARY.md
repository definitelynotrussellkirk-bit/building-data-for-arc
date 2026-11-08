# a1c55d0f7af9

Grid with bg = color 7. Contains: (a) 1-3 ANCHOR cells (color 9); (b) 2-5 OBJECTS, each a small connected blob (2-4 cells) in some non-{7, 9} color. Anchors and objects are separated (≥1-cell buffer). Rule: for each object O, find the nearest color-9 anchor cell (Manhattan). Compute dominant direction (whichever axis has larger offset; ties go to row). Slide O entirely until its bounding box touches the grid edge in that direction. Anchors stay put; bg preserved.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
