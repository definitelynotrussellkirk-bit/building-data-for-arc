# Solve work log

Earlier task-specific rule exposure: **no**. I had not opened any generator,
canonical rule, reference solution, audit evidence, or private query labels before
this attempt. I used only the visible examples printed by `review.py blind prepare`.

## Revision 1 — bounding-box perimeter for each colour pair

Each nonzero colour appears exactly twice. In all three demonstrations, the two
cells of one colour are opposite corners of an axis-aligned rectangle, and the
output colours the rectangle's perimeter while leaving its interior and all other
cells unchanged. Degenerate two-row or two-column rectangles appear filled simply
because every cell belongs to the perimeter.

Checks against the visible examples:

- colour 8 in train 2 spans a 3×3 box and becomes its eight-cell perimeter;
- colour 6 in train 2 spans rows 3–6 and columns 2–11, whose perimeter has
  `2*4 + 2*10 - 4 = 24` cells, matching the output count;
- train 1 independently shows 4×4, 2×2, and 2×4 boxes.

Implementation: collect positions by colour, copy the grid, and draw the top,
bottom, left, and right edges of the box joining each two-cell pair. I leave any
unsupported colour count unchanged rather than guessing beyond the visible domain.

Remaining uncertainty: hidden queries could contain coincident markers or more
than two cells of a colour, but all visible inputs consistently establish exactly
two distinct markers per colour.
