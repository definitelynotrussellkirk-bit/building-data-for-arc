# Visible-example solve log

Earlier exposure: yes. I had already reviewed the task's generator and rule before this required post-repair solve. During this solve phase I used only the public examples/challenge and did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Hypothesis

Each nonzero color forms one solid rectangle. The rectangles are read from left to right by their original horizontal positions, while their original vertical positions and gaps are discarded. They are redrawn on a zero canvas of the same dimensions as a staircase beginning at `(0, 0)`. After drawing a rectangle of height `h` and width `w`, the next rectangle starts at `(row + h - 1, column + w - 1)`, so adjacent rectangles share exactly one corner cell. The later rectangle owns that shared cell.

This explains the reduced count of every rectangle except the last: each earlier object loses its bottom-right corner when the next object is painted. It also explains all three visible outputs, including the tall/thin and wide/two-column objects.

## Implementation choice

For each nonzero color, collect its cells and recover the bounding-box height, width, and left edge. Sort these rectangle records by left edge, paint their full extents at the staircase cursor, and advance the cursor by `(h - 1, w - 1)`. Painting in sorted order implements later-corner ownership naturally.

## Limits considered

The visible examples use one solid rectangle per color and non-overlapping source objects. The implementation deliberately preserves the original canvas size and does not infer connected components separately for repeated colors, because no visible example supports multiple same-colored objects.
