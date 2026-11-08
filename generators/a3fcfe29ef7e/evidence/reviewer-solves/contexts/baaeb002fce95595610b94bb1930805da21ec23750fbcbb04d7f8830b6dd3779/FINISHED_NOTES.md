# Solve notes

## Visible-example hypothesis

Every input has two aligned three-column panels, in columns 0–2 and 4–6,
separated by a constant column 3.  The output keeps the input height, discards
the separator and compresses to three columns.

For each aligned pair `(r,c)` and `(r,c+4)`, the output is 3 exactly when both
input values are zero; otherwise it is zero.  I checked this against all four
visible examples, including the equal-foreground example where a nonzero/nonzero
pair must remain zero.  Colors themselves do not matter beyond zero versus
nonzero.

## Implementation

Construct a fresh `height x 3` grid and apply the pairwise Boolean NOR test.
No failed revision was needed.  I had already inspected the generator and rule
during repair, so this is an exposed post-repair solve, not a blind solve.
