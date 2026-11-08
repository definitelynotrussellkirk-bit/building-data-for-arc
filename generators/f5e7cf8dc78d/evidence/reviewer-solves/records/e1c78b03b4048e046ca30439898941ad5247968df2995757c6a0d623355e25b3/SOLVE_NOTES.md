# Solve work log

## Exposure declaration

Before this solve I had not opened task `f5e7cf8dc78d`'s generator, Racket rule,
notes, reference solutions, private query labels, or earlier solve explanations.
I used only the visible examples printed by `python3 review.py blind prepare` and
the files in `WORK/solve-blind/`.

## Revision 1 — nearest-row framed bands

Observation: every nonzero input cell is isolated. In every training output, the
seed's row becomes a full-width horizontal line in the seed color. The top and
bottom rows are also full-width lines, using the color of the nearest vertically
placed seed. All remaining output cells are zero except the first and last column.
Those two side-wall cells use the color of the nearest seed row. When a row is
exactly halfway between two seed rows, the upper seed wins (for example, training
example 2 row 5 between seed rows 4 and 6, and row 8 between rows 6 and 10).
The seed column appears deliberately irrelevant.

Implemented this rule directly. Remaining uncertainty: the visible examples do
not show two differently colored seeds on the same row or an input with no seeds;
the program assumes ordinary generated cases have distinct marker rows and
returns an unchanged all-zero grid for the degenerate no-seed case.
