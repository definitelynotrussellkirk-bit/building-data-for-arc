# Solve work log

Earlier exposure: none to this task's rule, generator, reference solution, labels, or prior solution notes. I used only `solve-blind/challenge.json`.

## Revision 1 — normalized red shape stamped at the green top-left

Across all three demonstrations, color 2 forms a small shape and color 3 forms a solid rectangular target area. The output clears the canvas, preserves the color-2 shape without rotation or reflection, translates its bounding-box origin to the top-left cell of the color-3 rectangle, and recolors the copied cells to 8. Empty cells inside the target rectangle remain 0.

I implemented this directly: collect cells of colors 2 and 3, normalize the red cells by the red bounding-box origin, anchor those offsets at the green bounding-box origin, and emit only color 8 on an otherwise-zero grid. The two visible queries fit this rule and the red shape fits inside the green rectangle in each case.

Remaining uncertainty: the examples do not show multiple red or green components, nonrectangular green regions, or a red shape larger than the target. The implementation follows the demonstrated color-specific contract and safely clips only if an unseen malformed case exceeds the canvas.
