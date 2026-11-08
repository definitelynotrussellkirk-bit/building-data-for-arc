# Post-repair visible-example solve

## Exposure disclosure

Earlier rule exposure: **yes**. Before this separate episode I worked on tests
and code review for the repaired generator and saw its intended transformation.
This is therefore not an unexposed discovery claim. During this solve I opened
only the new `README.md` and `challenge.json`, plus required command feedback.
I did not reopen the generator, Racket rule, prior explanations, canonical
helpers, private labels, or review evidence. No reference was consulted during
this solve.

## Visible hypothesis

The full color-9 row and column divide each grid into four panels. The top two
panels demonstrate a clockwise quarter-turn of an object within its own tight
bounding rectangle. The output retains every existing cell and fills the
bottom-right panel with that same operation applied to the bottom-left object,
using its original color.

Placement preserves the source bounding box's offsets from its panel's top and
left edges. Example 0 has source offsets (0, 0); example 1 has (1, 0), and its
target also starts one row below the lower panel's top; example 2 has (0, 1),
and its target starts one column to the right of the target panel's left edge.
These examples distinguish preserved offsets from always placing at the corner.
The source colors include both 4 below the upper color and 7 above it, so the
source panel determines the copied color. The lower shapes themselves determine
the answer; copying the upper object would disagree with the outputs.

For a source cell at coordinates (r, c) relative to its tight bounding box of
height h, clockwise rotation gives (c, h - 1 - r). I then add the original
source offsets and the bottom-right panel's origin. Detecting the actual divider
row and column also handles the public 12-by-12 query without assuming all four
panels have equal dimensions.

## Candidate 1 and query predictions

The new `solution.py` implements that coordinate transformation on a copy of
the input. It imports no helper, data, generator, or reference implementation.
It reads only lower-left foreground coordinates after locating the cross.

Public query 0: add color 8 at (7, 7), (7, 8), (7, 9), and (8, 9).
Public query 1: add color 2 at (7, 7), (8, 7), (8, 8), (8, 9), and (9, 8).
Coordinates are zero-based; all original cells are retained.

## Attempt history and stopping criterion

This is the first candidate. There have been no prior attempted or discarded
revisions in this episode. I will submit it with intent `solve`; the saved check
receipt records the visible matches and execution status. If all three visible
examples pass and query execution completes, the examples establish both the
rotation and separate row/column offsets, so I will finish without consulting
withheld answers. Private query correctness remains unknown to me.
