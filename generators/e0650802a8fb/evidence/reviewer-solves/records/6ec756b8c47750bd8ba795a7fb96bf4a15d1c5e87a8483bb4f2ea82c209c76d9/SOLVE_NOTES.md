# Visible-only solve notes

This is a human work log written after reading only `solve/challenge.json` during
this solve phase. I had earlier rule exposure from reviewing the assigned
generator, so the final exposure declaration is `yes`; I did not reopen or
consult the generator, Racket source, private labels, or prior solution notes
while writing this solver.

## Hypothesis from the five visible examples

- For each nonzero color, collect every occurrence in the original input.
- A color acts only when it occurs exactly twice and those two cells are on a
  nontrivial 45-degree diagonal (`abs(dr) == abs(dc)`).
- Paint the whole inclusive diagonal segment in that color.
- The mixed example shows that singleton, triple, and axis-aligned colors remain
  inert, establishing both the exactly-two and diagonal guards.
- The crossing example shows sequential overwrite behavior. Processing colors in
  row-major first-appearance order matches the visible ownership at crossings.

## Implementation

`solution.py` copies the input, records row-major first appearance and positions,
then fills qualifying paths in that order. It uses only original-input positions
to decide which colors qualify, so an earlier paint cannot change a later
color's endpoint count.
