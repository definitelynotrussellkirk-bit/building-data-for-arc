# Solve work log

## Prior exposure

Before this visible-only solve I had already reviewed the assigned generator and
canonical rule while repairing its public call contract, so earlier rule exposure
is **yes**. During this solve I did not reopen the generator, Racket source,
reference solutions, private query labels, or earlier solution explanations.

## Revision 1

The three demonstrations contain two to four separated, fully nonzero 3x3
blocks in a zero background, and every output is one of those blocks unchanged.
Counting color 1 inside each candidate explains all outputs: example 0 selects
the all-1 block; example 1 selects the block with five 1s over blocks with one
and two; example 2 selects the block with seven 1s. My hypothesis is therefore:
find orthogonally isolated all-nonzero 3x3 tiles, select the one with the largest
number of color-1 cells, and preserve row-major order if a tie occurs.

I implemented a direct scan with explicit boundary/isolation checks. For query 0
this predicts the middle all-1 tile. For query 1 it predicts the upper-right
all-1 tile over the upper-left seven-1 tile and lower-left one-1 tile. Remaining
uncertainty is limited to unseen tie behavior; row-major-first is the simplest
stable convention and does not affect the displayed examples.
