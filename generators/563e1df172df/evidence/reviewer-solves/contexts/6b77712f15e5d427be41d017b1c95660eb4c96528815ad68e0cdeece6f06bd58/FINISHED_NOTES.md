# Solve work log

## Prior exposure

Before this blind episode I accidentally opened only packet-level process/design documentation (`WELCOME.md`, `RETURN-GUIDE.md`, `ARC-DESIGN.md`, repository guides). I did not open task `563e1df172df`'s generator, canonical rule, private labels, reference solution, task notes, or prior solve explanation.

## Revision 1 — row of red, column of green

Hypothesis: the output preserves the unique red (`2`) and green (`3`) cells and draws an azure (`8`) Manhattan path between them. The bend is fixed at `(red_row, green_column)`: first traverse horizontally along the red cell's row to the green cell's column, then vertically along that column to the green cell.

Evidence from the four visible examples:

- Example 0: red `(7,3)`, green `(8,12)`; azure occupies row 7 through column 12, then reaches green vertically.
- Example 1: red `(0,14)`, green `(3,2)`; azure occupies row 0 back to column 2 and then column 2 down to row 2.
- Example 2: red `(4,2)`, green `(1,4)`; the elbow is `(4,4)`.
- Example 3: red `(8,10)`, green `(1,8)`; the elbow is `(8,8)`.

Alternative rejected: bend at `(green_row, red_column)`. Every visible output contradicts that orientation.

Implementation copies the grid, colors only zero cells on both inclusive line segments, and therefore preserves both endpoints. Before implementation, a direct visible-example assertion failed with the template's `NotImplementedError`, establishing the test was active.

Remaining uncertainty: none material for the two visible queries; both contain one red and one green marker on an otherwise empty grid.
