# Final-source post-repair solve notes

This is a human work log. I had earlier exposure to the task rule during generator review, so this episode is **exposed, not blind**. During this solve phase I read only `solve/challenge.json`; I did not reopen the generator, Racket source, reference solution, private labels, or the earlier solve explanation.

## Visible-example derivation

- Inputs contain a zero background, multiple monochromatic 4-connected components, and one singleton component.
- The singleton's color becomes the only nonzero output color.
- Each output preserves the holes and tight bounding-box shape of one multi-cell object, doubled in both axes.
- Training example 1 selects the 3-cell object over 5- and 7-cell objects, establishing minimum cell count.
- Training example 2 has two 5-cell minima; the one with the smaller bounding-box top row is selected.
- Training example 3 ties all three objects and selects the topmost one.
- Training example 4 has two 5-cell minima on the same broad row and selects the left one, establishing left-column tie-break after top row.

## Implemented hypothesis

Find same-color 4-connected nonzero components. Treat the unique singleton as the marker. Select the remaining component by `(cell_count, bbox_top, bbox_left)`, crop its exact bounding box while preserving zeros, recolor occupied target cells to the marker color, then repeat every row and column twice.

The implementation is independent of fixed dimensions, colors, locations, component count, crop size, or a particular morphology.
