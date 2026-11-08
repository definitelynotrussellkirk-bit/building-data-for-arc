# Solve work log

## Exposure

I had not opened this task's generator, Racket rule, reference solution, private
labels, audit records, or earlier solution explanations. I used only the visible
examples in `README.md` / `challenge.json` and a local test over those examples.

## Hypothesis

Color 8 forms fixed walls. Within each column, every maximal vertical run of
non-8 cells is an independent chamber. All nonzero colors in that run fall
upward: preserve their top-to-bottom order, place them at the top of the run,
and fill the remaining cells below with 0. The 8 cells never move.

Evidence:

- In train 0, columns 2 and 4 each contain two colors separated by zeros; both
  pairs become adjacent at the top while staying in their original columns and
  order.
- In trains 2 and 3, horizontal 8 walls split the same column into separate
  runs. Colors move to the top of their own run rather than crossing the wall.
- In trains 1 and 4, vertical walls create side-by-side regions, but the same
  per-column operation explains every changed cell.

## Alternatives rejected

- Packing all colors row-major into each rectangular room fails because the
  outputs retain each color's original column.
- Applying upward gravity to a whole column while ignoring internal 8 cells
  fails trains 2 and 3 because colors do not cross horizontal walls.
- Sorting colors numerically fails repeated-column examples; their observed
  top-to-bottom order is preserved.

## Probe and revision

Before implementation I wrote `/tmp/test_blind_ed98575459d2.py`, which checks
all five visible training pairs plus a synthetic column containing two chambers.
Against the untouched scaffold it failed with `NotImplementedError`, as expected.
I then implemented the per-column segmented gravity rule with a copied output
grid and no task-specific dimensions or coordinates.

Remaining uncertainty is limited to unseen inputs using a different background
or wall meaning; every visible example consistently uses 0 as empty and 8 as an
immovable separator.
