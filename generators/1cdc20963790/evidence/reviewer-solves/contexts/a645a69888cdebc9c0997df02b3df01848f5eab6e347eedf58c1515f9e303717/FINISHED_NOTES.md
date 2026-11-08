# Visible-only solve notes

## Observation

Every example preserves the first row and first column.  Interior zeros remain
zero.  The two marker colors behave differently:

- An interior `1` is replaced by the color at column 0 of the same row.
- An interior `2` is replaced by the color at row 0 of the same column.

For example, train 0 cell `(1,1)` changes from `1` to the row header `4`, while
cell `(1,5)` changes from `2` to the column header `8`.  Train 3 includes useful
identity cases: a `1` in the row headed by `2` becomes `2`, and a `2` below a
top header `2` remains `2`; these show that the marker value itself is not a
paint color.

## Hypothesis

Treat row 0 and column 0 as lookup tables.  Initialize a zero grid, copy those
headers, then dispatch each interior marker through the appropriate lookup.
Any other interior value is background under the visible grammar.

## Exposure disclosure

This is not a blind inference record: I had already reviewed the generator's
intended rule before this required post-repair solve.  During this solve phase I
used only the displayed examples and did not reopen the generator, Racket rule,
private labels, or reference solution.
