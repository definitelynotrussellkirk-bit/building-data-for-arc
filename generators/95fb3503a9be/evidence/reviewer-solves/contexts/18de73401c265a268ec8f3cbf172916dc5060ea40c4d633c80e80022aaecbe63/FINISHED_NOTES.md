# Solve work log

Earlier exposure before this solve: none to this task's generator, Racket rule,
private labels, reference solution, or prior solution explanation. I used only the
visible examples printed by `review.py blind prepare` / `challenge.json`.

## Revision 1 — crop and rank the objects

The input contains three separated monochrome objects on color 0. The output
preserves every colored cell, crops each object to its own bounding box, places
all crops top-aligned, and inserts one zero column between adjacent crops. The
objects are ordered by decreasing colored-cell count: examples 1 and 3 give
strict orders 6>5>4 and 7>5>3. Example 2 has two four-cell objects; the wider
T comes before the square, and its color is also smaller. Example 0 has a true
tie in both count and 3x3 bounding-box dimensions, with color 6 before color 8.
I therefore use ascending color as the deterministic tie-breaker. (A reverse
spatial-order tie-break also fits the visible ties, so tie semantics remain the
main uncertainty; query 0 does not distinguish those two readings.)

Implementation probe: find 4-connected same-color components, crop each bounding
box, sort by `(-cell_count, color)`, and concatenate on a canvas whose height is
the maximum crop height. I compared the implementation locally against all four
visible training pairs before submitting the revision.
