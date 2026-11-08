# Solve work log

## Exposure statement

Before this blind solve I had opened only the packet-wide instructions and lane assignment. I had not opened task `8f6a6ec3ae21`'s generator, canonical rule, notes, solutions, audit evidence, or private labels.

## Revision 1 — border selectors form a Cartesian product

Across all three training examples, color `2` cells on the top row identify output columns, while color `1` cells in the first column identify output rows. The output clears the input and writes color `8` at every selected-row × selected-column intersection. Border distractors of the opposite color are ignored: the color `2` in the first column of examples 0 and 2 does not select a row, and the color `1` on the top row of example 1 does not select a column.

I implemented exactly that rule, excluding the marker row and marker column from selection. The output shape is unchanged. Remaining uncertainty is limited to malformed/empty inputs outside the visible ARC task domain; the implementation handles empty grids and rejects ragged grids.
