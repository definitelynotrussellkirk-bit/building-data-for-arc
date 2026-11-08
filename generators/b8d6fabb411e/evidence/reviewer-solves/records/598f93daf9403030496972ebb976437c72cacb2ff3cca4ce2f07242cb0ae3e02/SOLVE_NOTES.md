# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
labels, prior notes, or audit records.  I used only `solve-blind/challenge.json`
and the packet's solve instructions.

## Revision 1 — orthogonal connection to the green rectangle

The examples contain one solid green (`3`) rectangle plus isolated markers in
one or two other colors.  Only markers sharing a row with the rectangle's row
span or a column with its column span change the grid.  The output fills the
zero-valued gap from each such marker to the nearest rectangle edge using the
marker color.  Markers not orthogonally aligned with the rectangle remain
unchanged.

Cross-example checks:

- Train 1: the `6` above column 4 and left of row 5 connect to the block; the
  `7` right of row 5 and below column 3 connect; all other markers are unaligned.
- Train 2: a `2` above the block and a `1` left of it connect by one cell each.
- Train 3: only the left-hand `6` shares a block row.
- Train 4: two `2` markers connect from above and left, and one `9` connects
  from below; the remaining markers share neither a block row nor column.

I implemented this directly, preserving every original cell and painting only
zero cells strictly between a marker and the green rectangle.  I did not add a
contrived failed revision because the same rule accounts for all four visible
training pairs.  Remaining uncertainty is limited to unseen cases with multiple
markers on the same ray or obstacles in a gap; the visible examples provide no
basis for overwriting nonzero cells, so the program conservatively leaves them.
