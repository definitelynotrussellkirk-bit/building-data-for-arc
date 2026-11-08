# Solve work log

## Prior exposure

Before this solve I had reviewed the selected generator and canonical Racket authority, so this is an **exposed** post-repair solve. I did not reopen either source, any reference solution, or private query labels during this solve.

## Revision 1 — nearest-color Manhattan partition inside the 8 bbox

Visible-example observations:

- The 8 cells identify a rectangular region by their minimum/maximum row and column. Some examples use a complete perimeter and one uses only four corners, so the bounding box rather than frame continuity is operative.
- Every nonzero, non-8 cell strictly inside that box acts as a colored seed; cells outside the box stay unchanged.
- The interior is partitioned into axis-aligned/diagonal stair-step regions consistent with Manhattan distance.
- Where two nearest seeds have different colors, the output remains 0. The fourth training example also contains two seeds of color 7, and equal-distance cells shared by those seeds still become 7, so the tie test is on the set of nearest **colors**, not the number of nearest seed cells.

Implementation hypothesis: for each interior cell, compute Manhattan distance to every seed. If the minimum-distance seeds have one distinct color, write that color; otherwise write 0. Preserve the 8 cells and all cells outside the bounding box. This single rule accounts for all four visible training pairs, including corner-only frames and same-color ties.

Remaining uncertainty before checking: none material; the examples directly distinguish full-ring-only, Euclidean-distance, and blanket-tie-blank alternatives.
