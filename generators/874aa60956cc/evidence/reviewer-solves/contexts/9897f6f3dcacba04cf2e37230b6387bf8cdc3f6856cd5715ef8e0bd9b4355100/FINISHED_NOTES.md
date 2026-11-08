# Post-repair visible-example solve

Earlier exposure: yes. I repaired this generator and examined its canonical rule before preparing this episode. This is an exposed solve, not blind. From preparation through finish I read only solve/README.md and my own Python solution; I did not reopen the generator, reference rule, previous solution explanations, or private query labels. These are an authored work log, not a token-level model trace.

Visible shapes: example 0 is 9 rows x 8 columns in and out; examples 1 and 2 are 9 rows x 10 columns in and out. The two queries each have a 9x10 input and unknown output dimensions.

The visible rule is to group the original input's coordinates by nonzero color. Colors occurring exactly twice identify rectangle bounds. Draw only their borders; a side of length two naturally gives a filled thin rectangle. Colors occurring once or three times do not themselves expand: example 1's 4 occurs three times and 5 once. Their original cells can still be overwritten by a later border.

At overlapping pixels, first appearance in row-major scanning orders the painting. Example 0, coordinate (3,1), begins as 7 but becomes 5. The first 7 precedes the first 5, although the second 7 comes later than the second 5. This rules out finishing-pair order and restoring original clues. The shape interior remains blank where no later border crosses it.

Implemented one straightforward Python attempt: record original positions in insertion order, copy the input, and paint each two-point group's four sides in that order. No deliberate failed attempt was created. I will stop after the visible examples pass and both queries execute; hidden correctness must remain independently scored.
