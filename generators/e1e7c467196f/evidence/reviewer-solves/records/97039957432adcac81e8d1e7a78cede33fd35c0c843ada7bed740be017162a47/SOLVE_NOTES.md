# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, reference solutions, private labels,
or prior notes for task `e1e7c467196f`.  I used only `solve-blind/challenge.json`.

## Revision 1 — two-row color lookup table

The first two rows begin with equally long nonzero runs.  Across the visible
examples, each column in that run behaves as a source → replacement pair:
`1→2, 7→6` in the first lesson; `1→5, 8→2, 7→4, 3→6` in the second; and
`9→4, 1→3, 7→5` in the third.  Occurrences below the table are replaced,
colors that are only targets or absent from the table stay unchanged, and the
two table rows are erased.

I implemented that rule by reading the shared nonzero prefix of rows 0 and 1,
building a dictionary, clearing the first two rows, and applying the dictionary
only to later rows.  An alternative interpretation—mapping every color found
in either top row—fails on visible cells such as color 2 and color 9 in the
second lesson, which correctly remain unchanged because they are not source
colors.  Remaining uncertainty is limited to whether a generated table can
contain background color 0 or non-table data elsewhere in the first two rows;
the visible format consistently uses 0 as the separator/background.
