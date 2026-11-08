# Solve notes

## Visible-example observations

- Every input has two equal-width panels separated by a full-height column of color 9.
- The output has the same shape as either panel.
- At each coordinate, a zero in the left panel produces zero in the output.
- A nonzero in the left panel keeps the value at the corresponding coordinate of the right panel.
- The left value itself is not copied: for example, the first training case has left value 2 at row 2, column 0 while the output is the right value 8.
- Training case 2 uses mask color 3 and training cases 1/3 use mask color 2, so the condition is “left is nonzero,” not “left equals 2.”

## Hypothesis

Find the unique full-height 9 separator. Split the grid into equal left and right panels. Return the right-panel value wherever the corresponding left-panel cell is nonzero; otherwise return 0.

## Implementation decision

The solver locates the separator rather than assuming a fixed width, validates the equal split, and applies the coordinate-wise mask. This directly explains every visible output cell and handles both visible test shapes.
