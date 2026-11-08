# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, canonical rule, reference solution, private labels,
or prior solve notes. I used only the visible examples produced by `review.py blind prepare`.

## Revision 1 — unique unobstructed horizontal pairs

Hypothesis: for each nonzero color that occurs exactly twice in the whole grid, fill the
inclusive horizontal interval between its two cells when they share a row and every
interior cell is background (`0`). Leave vertical pairs, colors occurring more than twice,
and pairs separated by a nonzero obstruction unchanged.

Evidence from the visible examples:

- Example 0 fills both color-5 and color-1 horizontal pairs; both colors occur exactly twice.
- Example 1 fills color 7, while color 2 is unchanged because it occurs four times.
- Example 2 fills color 5, while the color-4 pair is blocked by a color-2 cell.
- Example 3 fills color 7, while color 6 is vertical and color 1 occurs three times.

Before implementation I wrote a local regression containing all four visible training pairs
and observed the expected `NotImplementedError`. The implementation then passed that
regression. The two visible queries appear to require filling the color-7 and color-5 spans
in query 0, and the color-2 and color-6 spans in query 1. Private query labels were not
consulted.

Remaining uncertainty: the examples do not independently distinguish a globally unique
pair criterion from some more specialized selection rule that happens to agree on these
four lessons, but the distractors deliberately exercise multiplicity, orientation, and
obstruction, making the stated rule the most direct fit.
