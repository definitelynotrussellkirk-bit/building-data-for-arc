# Solve work log

I had not seen task `a9c4475d7cda`, its generator, its Racket rule, private
labels, or any previous solution explanation before this blind episode. I used
only the visible examples emitted by `blind prepare` and `challenge.json`.

## Revision 1 — compartment marker threshold

The color-8 full rows and columns divide every input into a 3 × 3 array of
compartments. I counted color-6 cells in each compartment across all three
training examples. Every output 1 corresponds to a compartment with two or
three 6-cells; every output 0 has zero or one. This supports the rule: emit a
3 × 3 binary summary with 1 exactly when a compartment contains at least two
markers.

I implemented divider-color inference from complete rows and columns rather
than hard-coding 8, then split the remaining row/column runs and counted all
non-background, non-divider cells. This is equivalent to counting 6 in the
visible data while remaining color-permutation tolerant.

Predicted queries before checking:

- Query 0: `[[0,1,0],[1,1,0],[0,0,1]]`
- Query 1: `[[1,1,1],[1,0,0],[0,0,1]]`

Alternatives considered and rejected from the visible examples: exact count 2
fails on training compartments with three markers and output 1; any-marker
presence fails on one-marker compartments with output 0; majority/area rules
are inconsistent across unequal compartment sizes. Remaining uncertainty is
whether unseen data could contain a second non-divider foreground color with a
different role, but all visible examples use only one marker color and the
structural count rule is exact on every training cell.
