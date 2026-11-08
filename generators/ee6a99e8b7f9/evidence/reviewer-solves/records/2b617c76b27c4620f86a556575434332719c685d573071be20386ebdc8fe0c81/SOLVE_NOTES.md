# Visible-only solve notes

This is a human work log. I had already inspected the task rule while repairing the generator, so this episode is **not blind**; during this solve I kept the generator, Racket source, reference answers, and previous solution explanations closed and used only `solve/challenge.json`.

## Hypothesis from the four demonstrations

- `8` is background, `9` is a marker, and each monochrome `5` or `6` component is a filled rectangle (including one-cell-wide/high cases).
- A `9` is attached to a rectangle only when it is orthogonally one cell outside an edge, with its other coordinate inside that edge's span.
- For a `6` rectangle, preserve the rectangle, erase the outside marker, and move the marker to the rectangle's centre row (for top/bottom markers) or centre column (for left/right markers), retaining the coordinate parallel to the contacted edge.
- For a `5` rectangle, erase the whole rectangle, retain the outside marker, and add a `9` on the immediately adjacent former rectangle cell.
- Multiple markers act independently; examples with non-3x3 rectangles and one-cell dimensions rule out a fixed two-step displacement.

## Implementation choice

First extract all `5`/`6` components and their bounding boxes from the unchanged input. Then collect source erasures and target marker writes, so clearing a gray rectangle or moving one marker cannot change the association decisions for another shape. No deliberate teaching negative was made because the first implementation directly represented the rule supported by all four examples.
