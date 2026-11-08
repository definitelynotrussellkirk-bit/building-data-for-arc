# Visible-only solve notes

This is a human work log based only on `solve/challenge.json` during this solve phase.
I had earlier exposure to the task family while reviewing the assigned generator, so
this is not a blind record; I did not consult the generator, Racket rule, reference
solutions, or private labels after preparation.

## Hypothesis

Each nonzero input cell is a colored seed. The output preserves the seed and paints
all in-bounds cells at Manhattan distance exactly two with the same color. The shape
is the eight-cell radius-two diamond when fully visible; border seeds produce clipped
diamonds. The examples with repeated color 2 show that equal-colored seeds still act
independently. I preserve original nonzero cells and only paint cells that remain zero,
processing seeds in row-major order in case two shells ever compete.

## Revision 1

Implemented the exact-distance-two rule directly with an immutable source copy and a
fresh output copy. No diagnostic or deliberately wrong revisions were needed because
all three visible examples distinguish the diamond shell from a filled disk, square
ring, and axial-only cross.
