# Solve work log

I used only the visible challenge, my own Python probes, and the visible-only
checker. I did not open the generator, Racket rule, reference solutions, private
query labels, prior task notes, or audit evidence before finishing this solve.

## Observations and hypotheses

The output dimension equals the number of nonzero colors, with rows and columns
ordered by ascending color value. The matrix is symmetric and its diagonal is
zero.

My first hypothesis was geometric containment: for each pair, write the color of
the object that could contain the other shape under translation. A visible-only
Python probe matched training examples 0 and 1 but failed training example 2 at
the pairs involving color 8. That failure exposed a simpler invariant: every
off-diagonal entry is the color whose object has more occupied cells; equal-size
objects produce 0. This cell-count comparison matches every visible training
entry, including the otherwise troublesome 4-vs-8 and 6-vs-8 pairs.

## Implementation and checks

The solver counts all cells of each nonzero color, sorts the colors numerically,
and constructs the pairwise winner matrix. A temporary test first failed on the
stub (`NotImplementedError`), then exercised all three visible examples plus a
synthetic equal-count/order case. The implementation was written only after that
expected failure.

Remaining uncertainty is limited to unseen conventions not represented by the
examples (for example, a nonzero background). All visible inputs use 0 as the
background and all outputs use 0 for ties/diagonal, so the implementation follows
that demonstrated contract rather than inventing a broader one.
