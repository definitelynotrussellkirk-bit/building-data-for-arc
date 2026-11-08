# Visible-example solve log

Earlier exposure: **yes**. I repaired this task's generator before this episode, so this is not a blind solve. During this solve I used only the displayed examples and did not open or consult the Racket rule, generator source, private labels, reference solutions, or prior solve explanations.

## Hypothesis

Every nonzero four-connected monochromatic object is a filled rectangle with odd height and odd width. The output is a fresh zero grid of the same shape. For each rectangle, retain its complete middle row and complete middle column in that rectangle's color, producing a cross. Process all rectangles simultaneously.

Evidence from the visible examples:

- A 3×5 rectangle becomes 7 colored cells: five across plus three down minus the shared center.
- A 3×3 rectangle becomes 5 cells.
- A 5×3 rectangle also becomes 7 cells, showing that both axes, not only the longer one, are retained.
- Objects can be close diagonally, so I segment by same-color 4-connectivity rather than by a global color bounding box or 8-connectivity.

## Implementation

Scan the grid, flood-fill each nonzero same-color 4-connected object, compute its bounding box, then paint that bbox's middle row and middle column into a fresh zero grid. This directly covers both visible queries, including the 5×5 and 3×3 objects in query 0 and the 3×5 plus 3×3 objects in query 1.

## Alternatives rejected

- Keep only the center cell: contradicted by every visible output.
- Keep only the middle row or only the middle column: contradicted by the perpendicular arms.
- Transform only squares: contradicted by 3×5 and 5×3 examples.
- Use one bounding box per color: unnecessary and fragile if a color appears in separated objects; object-wise 4-connectivity matches the displayed structure.
