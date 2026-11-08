# Solve work log

## Prior exposure

I had not opened the generator, canonical rule, reference solution, private labels,
or any earlier explanation for task `7d8fc2325e02`. I used only the visible examples
printed by `python3 review.py blind prepare` and the generated visible-only README.

## Revision 1 — cellwise union of two panels

Each 9-row input contains two 4-row panels separated by one solid horizontal row.
The output has the panel dimensions. Treating every nonzero cell in either panel as
occupied reproduces all three outputs: an output cell is color 3 exactly when the
corresponding top-panel cell or bottom-panel cell is nonzero; otherwise it is 0.
The separator color and the two panel colors therefore act only as structural/object
colors and are discarded.

I first wrote an independent visible-example test for all three training pairs and
confirmed that the starter `NotImplementedError` failed it. I then implemented the
minimal rule: split around the middle row, zip corresponding cells, and emit 3 for
the Boolean OR of their nonzero masks. The same geometry also handles query 0 even
though its separator and panel marks all use color 3, because the separator position
is determined by the two equal 4-row panels rather than color identity.

Remaining uncertainty: the visible examples do not distinguish a fixed midpoint
split from searching for a solid separator row, but every shown input is exactly
9 rows with equal panels and the required output height is 4, so the midpoint is the
simplest rule consistent with all evidence.
