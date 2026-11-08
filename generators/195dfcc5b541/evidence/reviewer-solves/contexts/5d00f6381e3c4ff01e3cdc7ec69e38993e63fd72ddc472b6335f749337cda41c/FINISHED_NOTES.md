# Solve work log

## Prior exposure

Before this solve I had read only the packet's general workflow documents and the
drawn duty text. I had not opened task `195dfcc5b541`'s generator, Racket rule,
notes, reference solution, private labels, or audit evidence.

## Revision 1 — shape-template hypothesis

The only output changes in all three visible examples are `3 -> 8`. The input's
existing color-8 cells form a small template. Each changed group of color-3 cells
is congruent to that template after translation, rotation, and/or reflection;
all unrelated color-3 cells remain unchanged.

I used a challenge-only Python probe to normalize the color-8 coordinates,
generate their eight dihedral transforms, scan each visible input for exact
color-3 occupancy in the transformed bounding box, and compare the union of
matched cells with the visible input/output differences. The probe found exactly
three copies in every training example and reproduced all changed cells with no
extras or misses (15 cells in example 0; 12 each in examples 1 and 2).

`solution.py` therefore extracts the color-8 template, scans the original grid
for exact color-3 copies under all rotations/reflections, unions overlapping
matches, and recolors those cells to 8. Exact bounding-box occupancy avoids
mistaking a candidate with an extra color-3 cell for the demonstrated shape.
Remaining uncertainty: the visible data do not distinguish exact-bounding-box
matching from a weaker required-cells-only rule, but both agree on every shown
example and the exact interpretation better preserves the demonstrated object.
