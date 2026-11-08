# Solve work log

## Exposure declaration before solving

I had not opened task `b985d561c63b`'s generator, Racket rule, notes, reference
solutions, private labels, or audit evidence. I used only the public examples
printed by `python3 review.py blind prepare` and the generated solve files.

## Revision 1 — colored template stamped into gray canvases

**Observation.** Each input contains one compact pattern made from colors other
than 0 and gray (5), plus one or more solid gray rectangles. The output leaves
the source pattern in place and copies its full bounding rectangle into the
upper-left corner of every gray rectangle. Internal background cells are part
of the copied rectangle: train example 1 changes the lower-left copied cell
from gray to 0. Any unused bottom rows or right columns of a larger gray canvas
remain gray.

**Program.** Find the bounding box of all cells whose colors are neither 0 nor
5. Extract that rectangle exactly, including internal zeros. Find each
4-connected gray component, require it to be a solid rectangle large enough for
the template, and stamp the template at its upper-left corner.

**Alternatives considered.** Recoloring all gray cells, tiling the pattern, and
matching source/target dimensions do not explain train example 1, where a 3×2
pattern is placed once in each 4×3 gray block and the remaining row/column stay
gray. Alignment other than upper-left is likewise contradicted there.

**Remaining uncertainty.** The visible examples consistently use color 5 as the
canvas marker and one non-gray template. The implementation deliberately skips
nonrectangular or too-small gray components rather than guessing behavior not
shown by the examples.
