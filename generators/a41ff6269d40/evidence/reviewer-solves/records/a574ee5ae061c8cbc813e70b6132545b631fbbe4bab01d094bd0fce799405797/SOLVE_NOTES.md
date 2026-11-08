# Solve work log

## Prior exposure

Before this blind episode I had not opened this task's generator, Racket rule,
canonical record, solutions, audit evidence, or any earlier explanation. I used
only the visible examples printed by `review.py blind prepare` and the local
visible-example checker.

## Revision 1 — diagnostic baseline

I first ran the provided `NotImplementedError` scaffold as a diagnostic/TDD red
step. It errored on all three visible examples, as expected; this was not a rule
hypothesis.

## Revision 2 — template stamping hypothesis

The color-4 cells form one tight rectangular template. The output removes the
source and all marker colors, then stamps a color-4 copy with its top-left corner
at every marker:

- marker 1: template unchanged;
- marker 2: horizontal reflection;
- marker 3: vertical reflection.

Evidence from the examples:

- Example 1's 4×3 seven-cell object appears unchanged at marker 1, mirrored
  left/right at marker 2, and mirrored top/bottom at marker 3.
- Example 0 initially looked shifted, but using the *tight* bounding box of the
  color-4 cells gives the 2×3 template `44 / .4 / .4`, which aligns exactly at
  all three marker coordinates after the corresponding reflection.
- Example 2 independently confirms the same anchor convention and transforms.

The first query has two marker-2 cells, so the implementation deliberately
supports repeated markers of a color. It clips a stamped cell at the grid edge;
the visible examples place every copy fully in bounds, so clipping remains an
untested defensive choice rather than part of the inferred rule.
