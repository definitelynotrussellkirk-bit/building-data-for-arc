# Blind solve work log

## Revision 1 — aligned equal-color pairs

Observed rule from the four visible demonstrations:

- For each nonzero color that occurs **exactly twice**, connect its two cells
  when they lie in one row or one column, filling the inclusive straight segment.
- A color occurring another number of times is left alone (the three 8s in the
  fourth demonstration).
- A diagonal pair is left alone (the two 2s in the fourth demonstration).
- Both demonstrated segment crossings show color 8 over colors 2 and 4.  The
  simplest data-consistent compositing rule is numeric maximum at a crossing.

Predictions: test 1 gains horizontal 4 and 8 segments plus a vertical 5 segment;
test 2 gains a vertical 3 and horizontal 6 segment, with 6 at their crossing.
No reference program, generator, prior explanation, or private label was read.
