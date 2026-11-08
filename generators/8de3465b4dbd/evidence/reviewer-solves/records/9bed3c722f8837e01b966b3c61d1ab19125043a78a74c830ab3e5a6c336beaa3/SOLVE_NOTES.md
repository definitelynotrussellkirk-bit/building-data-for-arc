# Solve work log

## Exposure declaration before solving

I had not opened task `8de3465b4dbd`'s generator, Racket rule, private labels,
reference solution, audit records, or any earlier explanation. I used only
`solve-blind/challenge.json` and local Python checks.

## Revision 1 — horizontal completion marker

Hypothesis: every horizontal occurrence of `2,3,0` becomes `2,3,8`. A reversed
`3,2` pair is unchanged, and a `2,3` pair already followed by a nonzero cell is
also unchanged. This accounts for every changed and unchanged colored fragment
in all three visible training examples, including the `2,3,3` counterexamples.

Before implementation I ran an inline visible-example harness against the
provided template and observed the expected `NotImplementedError`. I then wrote
a minimal row-wise implementation that copies the grid and tests the original
row, so newly written 8s cannot create secondary matches.

Predicted test changes:

- Test 0: add 8 after the `2,3` pairs at rows 0, 1, 3, and 8; leave the reversed
  pair on row 6 unchanged.
- Test 1: add 8 after both unblocked pairs on row 0 and the pair on row 8; leave
  the `2,3,3` fragments and reversed pair unchanged.

Remaining uncertainty is low: the visible examples directly exercise repeated
pairs, vertical repetition, reversed orientation, edge placement, and blocked
third cells. The only unobserved case is a pair ending at the right boundary,
where there is no blank cell to recolor and the implementation correctly does
nothing.
