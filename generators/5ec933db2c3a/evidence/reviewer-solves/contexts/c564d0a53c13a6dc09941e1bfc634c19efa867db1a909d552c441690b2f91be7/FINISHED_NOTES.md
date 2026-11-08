# Solve work log

No generator, Racket rule, reference solution, private label, audit record, or
assigned-task source was opened before this solve. I only used the visible grids
printed by `python3 review.py blind prepare` and the files in `solve-blind/`.

## Revision 1 — rotational two-hole completion

The full-height color-9 column separates a narrow template panel from a larger
output panel. The nonzero cells in the left panel form a 3×3 template containing
six color-2 cells and one color-7 cell. The right panel has four 3×3 corner
blocks. Across all three demonstrations, the output changes exactly those corner
blocks that are compatible with a *rotation* of the template and are missing
exactly two of its nonzero cells. Blocks missing one or three cells are retained.
Reflections are not needed: in the third demonstration the ambiguous-looking
bottom-right fragment is completed as the rotational target, not its reflected
alternative.

I manually checked all twelve demonstration blocks by counting absent template
cells. The implementation finds the separator, crops the left template to its
nonzero bounding box, generates its four rotations, and repairs each corner
block only when all observed nonzero cells agree and exactly two target cells are
missing. Remaining uncertainty is limited to whether unseen instances ever place
candidate blocks away from the four corners; every visible example uses the four
corner layout with a blank central corridor.
