# Solve work log

## Exposure declaration

Before this post-repair solve I had already inspected the assigned generator and
canonical rule as part of the required repair work, so earlier rule exposure is
**yes**. During this solve I did not reopen the generator, Racket rule, reference
solutions, private query labels, or earlier solution explanations. I used only
the prepared visible challenge, my Python solution, and checker feedback.

## Revision 0 — required failing-first check

The prepared template raised `NotImplementedError`. I imported it against train
example 0 from `challenge.json`; the visible-example assertion failed at that
exception, confirming the test exercised the unimplemented solver rather than
passing vacuously.

## Visible-example observations

Every input has a positive even height. Splitting it horizontally gives two
panels of equal dimensions and different nonzero colors. Each output has one
panel's height, the same width, and only colors 0 and 4.

I compared aligned cells in the upper and lower panels. In all three training
examples:

- output 0 occurs only when both aligned input cells are 0;
- output 4 occurs when the upper cell is nonzero, the lower cell is nonzero, or
  both are nonzero;
- the identities of the two input foreground colors do not affect the result.

This is an occupancy union (Boolean OR), not XOR: train example 0, row 0 column
0 has nonzero cells in both halves and still outputs 4. It is not AND because
many positions occupied in only one half also output 4.

## Revision 1 — implementation

Implemented `solve(grid)` by splitting at `len(grid) // 2` and returning color 4
where either aligned cell is nonzero. I added basic positive-even-height and
rectangular-grid validation so malformed inputs fail explicitly instead of
silently truncating.

Local visible-only verification compared the implementation against all three
training outputs. The next step is the packet solve checker; no query labels are
used by the local test.

## Remaining uncertainty

The visible examples strongly determine the intended transformation within this
family. The main residual uncertainty is only outside the displayed domain—for
example odd-height or ragged grids—which the solver rejects rather than guessing.
