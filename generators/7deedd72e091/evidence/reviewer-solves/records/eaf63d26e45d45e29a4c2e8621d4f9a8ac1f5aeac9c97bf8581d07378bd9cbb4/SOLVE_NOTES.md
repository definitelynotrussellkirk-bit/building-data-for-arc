# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, notes, reference solution,
private labels, or audit evidence. I used only the visible examples printed by
`python3 review.py blind prepare` and my own scratch calculations.

## Revision 1 — congruent-panel equivalence matrix

The input is three small grids separated by full-height color-9 columns. At
first I considered color grouping and pointwise Boolean overlays, but those did
not explain the outputs. The useful invariant was that every output is a
symmetric 3×3 matrix with the diagonal filled and exactly one off-diagonal pair
filled. Thus it identifies an equivalent pair among the three panels.

Ignoring position, orientation, reflection, and object color, the indicated
pair contains the same finite cell shape:

- train 0: panels 0 and 1 are congruent; output marks pair (0,1),
- train 1: panels 0 and 2 are congruent; output marks pair (0,2),
- train 2: panels 1 and 2 are congruent; output marks pair (1,2).

I canonicalized each panel's occupied coordinates over all eight square
symmetries, normalizing translation after each transform. The solution returns
an 8 wherever two canonical signatures match, including the diagonal, and 0
otherwise. This predicts pair (0,1) for query 0 and pair (0,2) for query 1.

Remaining uncertainty: I assume separator columns are the full-height 9-columns
shown in every visible example, and that all nonzero cells inside a panel belong
to its shape. The program supports any number of such panels even though only
three are shown.
