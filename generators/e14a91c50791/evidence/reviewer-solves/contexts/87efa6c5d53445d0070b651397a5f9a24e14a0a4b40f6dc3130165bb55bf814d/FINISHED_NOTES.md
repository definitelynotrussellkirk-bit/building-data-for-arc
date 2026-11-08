# Solve work log

I had not opened the assigned repair generator, either task's Racket rule, any
reference solution, private labels, prior solve explanation, or task notes before
this solve. I used only `solve-blind/challenge.json` and small local component
measurements over that file.

## Revision 1 — odd multiplicity under shape congruence

I decomposed each training input into 4-connected color-2 objects and normalized
each object up to translation, rotation, and reflection. In every example, shape
classes with even multiplicity are left unchanged, while the single odd-count
class is transformed: count 1 for the 2x2 square in train 0, count 3 for the
corner-L pentomino in train 1, and count 1 for the stair tetromino in train 2.
The transformed objects are replaced by solid color-7 bounding rectangles.

This also explains why the identical stair tetromino is unchanged in train 1
(two congruent copies) but changed in train 2 (one copy), which rules out a
shape-only selection rule. A weaker "unique object" hypothesis fails train 1,
where all three congruent L objects change. A size-only rule also fails because
objects of the same size can have different outcomes.

The implementation groups 4-connected monochrome components by a dihedral
canonical key, selects every class with odd cardinality, and fills every member's
axis-aligned bounding box with 7. Remaining uncertainty: the examples imply one
odd class, but the code applies the parity rule independently if several odd
classes occur.
