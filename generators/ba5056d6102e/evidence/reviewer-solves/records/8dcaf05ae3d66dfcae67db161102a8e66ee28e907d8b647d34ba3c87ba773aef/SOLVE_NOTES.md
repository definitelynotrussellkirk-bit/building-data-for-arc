# Solve work log

## Exposure declaration

This is the required post-repair solve. I had already inspected and repaired the
`ba5056d6102e` generator and therefore had earlier rule exposure. During this
solve episode I consulted only `solve/challenge.json`; I did not reopen the
generator, Racket rule, reference solutions, private labels, or prior solution
explanations.

## Revision 1 — occupancy intersection

All three visible inputs consist of two equal-height panels separated by one
solid nonzero row. The foreground colors vary across examples, including a
role reversal: color 3 appears in the bottom panel of the first example and in
the top panel of the third. This makes color identity look irrelevant.

Comparing outputs coordinate by coordinate, an output cell is color 8 exactly
when the aligned cells in both panels are nonzero. Cells occupied in only one
panel and cells empty in both become 0. I checked the intersection, union, and
xor hypotheses against all visible examples: intersection fits all three;
union and xor fit none.

The implementation finds the centered solid nonzero separator, splits the grid,
and returns the Boolean occupancy intersection. It validates rectangularity and
requires a unique centered separator rather than guessing between multiple rows.

Remaining uncertainty is limited to out-of-domain malformed inputs (for example,
multiple centered separators). The visible lesson itself is unambiguous.
