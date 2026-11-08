# Solve work log

## Exposure

Before this solve I had not opened the Racket rule, generator implementation,
reference solutions, private query labels, prior solution explanations, or the
assigned repair generator. I used only the displayed examples and
`solve-blind/challenge.json`.

## Revision 1 — exact-two same-color row completion

Hypothesis: process rows independently. A row changes only when it has exactly
two nonzero cells and both have the same color; replace every cell from the
left marker through the right marker with that color. Leave rows with zero/one,
three or more nonzero cells, or two different colors unchanged.

Evidence from the visible examples:

- Example 0 fills the two-4, two-6, and two-8 rows. It does not fill the row
  with three 7s or the row containing different colors 2 and 3.
- Example 1 is the discriminating case against “fill any same-color pair”: the
  row containing one 3 plus two 1s remains unchanged because it has three
  occupied cells. Only the rows consisting of exactly two 2s and exactly two
  3s are filled.
- Example 2 fills rows consisting of exactly two 9s, two 5s, or two 4s, while
  preserving a two-different-color row and a row with three 5s.

I first wrote `blind_visible_test.py` outside the return workspace to assert all
three visible train pairs. It failed on the provided `NotImplementedError`, as
expected. I then implemented the minimal row rule without mutating the input.

Predicted query changes:

- Query 0: fill row 2 from columns 6–8 with 4 and row 6 from columns 2–8 with
  6; leave the other rows unchanged.
- Query 1: fill row 1 columns 6–10 with 8, row 2 columns 6–8 with 6, and row 3
  columns 6–10 with 5; leave the three-6 row and mixed 7/4 row unchanged.

Remaining uncertainty: the examples strongly distinguish the cardinality gate,
but only horizontal rows are represented. I did not generalize to columns or
other backgrounds because doing so would add behavior unsupported by the
visible data.
