# Solve work log

## Exposure statement before solving

I had already inspected the selected generator and canonical Racket rule during
the required review phase, so earlier rule exposure is **yes**. During this
fresh solve phase I used only `challenge.json`, my own Python, and check feedback;
I did not reopen the generator, rule, reference solution, or private query labels.
This is a human-authored work log, not a token-level model trace.

## Revision 0 — visible-only hypothesis

Across all four visible demonstrations, the four gray cells define the extrema
of an axis-aligned square: three gray cells are square corners and the fourth is
inside. The absent square corner is the apex of a triangle. Paint orange cells
with color 8 along the two square sides incident to that absent corner and along
the diagonal joining the two opposite present corners. Preserve all gray cells
and all cells outside those three boundary segments.

I encoded this in square-local coordinates from the missing corner. Boundary
cells satisfy `u == 0`, `v == 0`, or `u + v == side`; this avoids separate cases
for the four orientations. Remaining uncertainty is limited to malformed inputs,
which are not shown in the visible episode.
