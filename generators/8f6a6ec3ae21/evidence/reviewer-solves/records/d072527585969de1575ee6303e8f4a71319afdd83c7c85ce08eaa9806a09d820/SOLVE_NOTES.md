# Solve work log

Earlier exposure: none. Before this blind phase I read only the packet-wide instructions and the assignment text; I did not open this task's generator, rule, private labels, notes, or prior solutions.

## Revision 1

Hypothesis: the first row and first column are independent headers. A `2` in the top row selects an output column, while a `1` in the left column selects an output row. The transformation clears the canvas and writes color `8` at every Cartesian-product intersection of those selected rows and columns.

Evidence from the visible examples:

- Example 0 has top-row `2`s at columns 1, 4, and 7 and left-column `1`s at rows 1, 2, 4, and 5; the twelve output `8`s are exactly those intersections.
- Example 1 includes a top-row `1` at column 7, which is correctly ignored, while columns 6 and 8 (both `2`) are projected onto the three rows marked `1`.
- Example 2 includes a left-column `2` at row 7, which is correctly ignored, while the two rows marked `1` intersect the three top-row `2` columns.

The cross-color distractors establish the orientation and values: this is not merely all nonzero edge-marker intersections. The implementation preserves the input dimensions and writes zeros everywhere else.

Remaining uncertainty: the visible data do not show ragged inputs or a nonzero top-left corner, but ARC grids are rectangular and the observed semantic distinction is strong enough to stop after this revision.
