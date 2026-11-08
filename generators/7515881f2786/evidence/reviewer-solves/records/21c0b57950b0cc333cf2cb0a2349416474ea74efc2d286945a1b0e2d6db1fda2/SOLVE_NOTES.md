# Solve work log

## Exposure record

I had not opened this task's generator, Racket rule, reference solution, private
labels, audit records, or earlier solution notes. I used only the visible grids
created by `python3 review.py blind prepare` and `challenge.json`.

## Revision 1 — shared row/column span completion

Across all four training examples, one or more azure cells share a row and one
or more share a column. The output preserves every original cell and fills the
inclusive interval between the leftmost and rightmost same-colored anchors in
each repeated row, plus the interval between the topmost and bottommost anchors
in each repeated column.

Examples supporting this:

- Train 0 fills row 0 from columns 1 through 7 and column 3 from rows 1 through 7.
- Train 1 fills row 0 from columns 0 through 6 and column 3 from rows 0 through 6.
- Train 3 shows that an unrelated point at `(3, 2)` is retained while the new
  vertical segment at column 3 passes beside it.

The spans must be detected from the original input. Detecting repeated lines
after drawing the first segment would create a cascade not present in the
training outputs.

The first query deliberately contains two repeated rows and two repeated
columns, so I generalized the rule to every original row/column containing at
least two anchors rather than assuming exactly one of each. I implemented the
same operation independently per non-background color and infer the background
as the most frequent color. Remaining uncertainty: the visible data has only
colors 0 and 8, but this color-independent formulation preserves the observed
object relation.
