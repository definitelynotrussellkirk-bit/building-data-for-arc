# Solve work log

I had earlier exposure to the task rule during generator review, so this is an
**exposed post-repair solve**, not a blind solve. During this solve episode I
used only the visible examples in `solve/README.md`; I did not reopen the
Racket rule, generator implementation, reference solution, private labels, or
previous solution explanations.

## Revision 1

Hypothesis from all four visible pairs: collect the distinct columns that
contain at least one zero, sort those columns from left to right, and assign
ranks 1, 2, ... in that order. Replace every zero in a column by that global
column rank; preserve every nonzero cell. The 14x15 example is especially
separating because it contains eight zero columns, and the same rank repeats
across rows despite different row-local zero subsets. The two-colour 12x16
example shows that nonzero colours are irrelevant and preserved.

Implementation directly computes the global column set and applies the rank map.
No alternative revision was needed. Remaining uncertainty is only masked-query
scoring, which the solve tool intentionally withholds.
