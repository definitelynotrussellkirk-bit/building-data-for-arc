# Solve work log

I had not opened this task's generator, rule, notes, reference solutions, private
labels, or any repair-generator source before solving.  I used only the visible
examples in `challenge.json` and small local Python probes over those examples.

## Revision 1 — stable sort of the variable columns

The grids consist of repeated vertical motifs: a constant foreground anchor
column, one column whose cells vary between foreground and zero, and one or more
all-zero separator columns.  I encoded only the varying columns as binary column
vectors and compared input with output.

For every training pair, each output varying column is exactly one whole input
varying column; rows are not independently edited.  The source-column order is:

- example 0: `[3, 2, 1, 0, 4]`, with foreground counts `[7, 8, 10, 11, 12]`;
- example 1: `[2, 1, 3, 0]`, with counts `[1, 4, 4, 7]`;
- example 2: `[1, 3, 0, 2]`, with counts `[4, 4, 7, 8]`;
- example 3: `[2, 3, 0, 1]`, with counts `[1, 4, 6, 10]`.

Thus the rule is to keep the fixed frame and stably sort the varying stripe
columns from fewest to most foreground cells.  Stability explains both tied
four-count columns.  `solution.py` identifies columns containing more than one
value, sorts them by nonzero count, and copies complete columns into the original
variable-column slots.  Remaining uncertainty is low: the query grids have the
same framed-stripe structure, though masked answers prevent direct confirmation.
