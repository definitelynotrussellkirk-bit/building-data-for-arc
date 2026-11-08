# Solve work log

## Exposure statement before solving

I had not opened this task's generator, Racket rule, canonical record, reference
solution, private labels, notes, or audit evidence. I used only the examples
printed by `python3 review.py blind prepare` and the visible solve files.

## Attempt 1 — four-way crossings

Observation: the output preserves every cell except selected `1` cells, which
become `2`. In every changed location, a horizontal color-1 stroke and a vertical
color-1 stroke continue through the same cell: there is an immediate `1` above,
below, left, and right. The examples deliberately leave T-junctions, L-shapes,
and a short vertical segment meeting a horizontal segment unchanged when one of
the four arms is absent.

Hypothesis: copy the grid and recolor exactly those color-1 cells having color-1
orth, south, west, and east neighbors. This predicts one marked crossing in query
0 at row 3, column 5, and two in query 1 at rows/columns (1, 2) and (7, 3).

Implementation: a single interior-cell scan over the original grid, so one newly
marked crossing cannot affect detection of another. Remaining uncertainty: the
visible data only uses background 0, stroke 1, and marker 2; I therefore keep the
rule literal rather than guessing a color-generalized variant.
