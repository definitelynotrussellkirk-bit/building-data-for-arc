# Solve work log

## Earlier exposure

Before this post-repair solve I had already inspected the assigned generator and
canonical rule while repairing it, so `earlier-exposure=yes`. During this solve I
kept those sources closed and used only the visible examples in `solve/README.md`
/`challenge.json` plus my own Python.

## Revision 1

Hypothesis from the visible pairs: color 9 is a hinge. Preserve the input and
copy every other nonzero cell to its reflection through the hinge's column when
the whole motif is strictly left or right of that column. Otherwise, when the
motif is strictly above or below the hinge row, reflect through the row.

Train 3 is the decisive priority case: its motif is both below and right of the
9, yet the shown output is a left/right copy, so the column-side test must run
before the row-side test. This also rules out the plausible row-priority rival.

I implemented that branch order directly. Query 0 therefore reflects the motif
above row 2; query 1 is both above and right of the pivot, so it reflects across
column 5. I did not consult private labels or any reference implementation.
