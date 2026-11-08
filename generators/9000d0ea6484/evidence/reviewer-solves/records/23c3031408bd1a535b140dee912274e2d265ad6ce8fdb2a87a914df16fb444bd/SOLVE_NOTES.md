# Solve notes — 9000d0ea6484

This is a human work log. I had already seen the task rule while repairing the
assigned generator, so this is **not blind**. During this solve phase I read only
the visible challenge and did not reopen the generator, Racket source, canonical
answers, or private labels.

## Visible-example derivation

The 19 columns split naturally into four 4-column blocks beginning at columns
0, 5, 10, and 15, with full color-3 separators at columns 4, 9, and 14. The
4-column output compares cells at the same offset within those four blocks.

Visible pairwise evidence establishes a fixed source priority:

- Train 0, row 0, output col 0: sources `(0,6,8,2)` produce `8`, so section 2
  outranks sections 1 and 3.
- Train 0, row 0, output col 1: `(0,6,0,2)` produces `2`, so section 3 outranks
  section 1.
- Train 0, row 0, output col 2: `(4,6,0,0)` produces `4`, so section 0 outranks
  section 1.
- Train 0, row 1, output col 3: `(4,0,0,2)` produces `2`, so section 3 outranks
  section 0.

Together these constraints give section order `2 > 3 > 0 > 1`. For each aligned
cell, return the first nonzero value in that order, otherwise zero. The Python
solution implements exactly this and preserves the input row count.
