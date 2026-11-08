# Solve notes

The input is three equal panels separated by two solid color-9 columns. The first two panels have a color label at local `(0,0)` plus a monochrome prototype. The third panel has an unlabeled query object.

Across the four visible examples, the output keeps the query object's exact displayed coordinates, changes only its color, and uses the label from whichever prototype has the same shape after translation, rotation, or reflection. The examples deliberately show both prototype labels and both orientation classes, so exact-coordinate matching and rotation-only matching are insufficient.

Implementation plan:
1. Find the two full-height 9 columns and recover the three panel offsets.
2. Extract each prototype while excluding its label cell.
3. Normalize supports by translation and generate all eight dihedral variants.
4. Match the normalized query to exactly one prototype.
5. Paint the query's original coordinates with that prototype's label color.

This is an exposed post-repair solve: I already knew the intended rule from generator review, but I did not consult the Racket source or private answers while writing this revision.
