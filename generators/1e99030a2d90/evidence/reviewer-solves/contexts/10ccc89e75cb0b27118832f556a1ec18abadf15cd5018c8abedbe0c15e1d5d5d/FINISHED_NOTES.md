# Post-repair visible-only solve

Task: 1e99030a2d90. Earlier exposure: **yes**. I inspected this task's
generator and canonical rule during the repair. This is an exposed authored
solve, not an independent blind measurement. During this solve phase I used
only the newly prepared challenge, a visible-data Python probe, and the
official visible-only checker. The generator, reference source, earlier
solutions, and private answers remained closed.

This is a reviewer-authored experiment summary, not a token-level model trace.

## Visible observations and probe

The demonstration input/output dimensions are respectively 10 x 10 / 10 x 10,
18 x 18 / 18 x 18, 11 x 11 / 11 x 11, and 16 x 22 / 16 x 22. A visible-data
delta probe found 3, 1, 1, and 1 changed cells. Each changed cell was 0 before
and 4 afterward, with red 2 immediately above, below, left, and right.
Orange 7 crosses, incomplete red crosses, and occupied red centers remain
unchanged. Some changed centers have nonzero diagonal neighbors, so an
isolated 3 x 3 template is unnecessarily restrictive.

## Hypothesis and revision 1

Copy the grid, then paint precisely the originally blank interior cells with
all four cardinal neighbors red. Read every predicate from the original grid;
preserve borders and other colors. Implemented that local rule directly in
Python and submitted it to the visible-only checker. There are no earlier
failed solve revisions to report. Query inputs are 10 x 10 and 11 x 18;
their output dimensions and correctness have not been disclosed.

## Checker result and stopping reason

Revision 1 completed and passed 4 of 4 visible demonstrations. The query
correctness label remains unknown. I stopped because the visible-data probe
and checker agree and there is no observed failure requiring a new revision.
