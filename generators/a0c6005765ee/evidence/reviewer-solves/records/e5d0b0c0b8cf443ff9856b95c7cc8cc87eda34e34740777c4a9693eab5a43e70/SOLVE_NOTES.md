# Solve work log

I had no earlier exposure to task `a0c6005765ee`, its generator, its Racket
rule, private labels, reference solutions, or prior solution explanations. I
used only `challenge.json` and local tests written against its visible training
pairs.

## Revision 1 — rectangle rays

Observation: every gray (`5`) component is a hollow axis-aligned rectangle.
Orange (`7`) cells sit immediately outside a side, aligned with an interior row
or column. The green (`3`) output is exactly the union of straight rays from
those markers through the rectangle interior: a marker above/below paints its
interior column; a marker left/right paints its interior row. The first example
has four markers and shows unions/crossings; the second has top plus left; the
third isolates a bottom marker.

I first added `test_solution.py`, which runs `solve` on all three visible
training pairs. It failed on the untouched `NotImplementedError`, establishing
a red test. I then implemented connected-component discovery for gray cells,
used each component's bounding box as the rectangle, copied the input, and
painted only zero-valued interior cells aligned with immediately adjacent orange
markers. This also handles the two separate rectangles in the first query.

Remaining uncertainty: the examples imply complete gray rectangular borders and
adjacent markers; there is no visible evidence for broken borders, diagonal
markers, or markers separated from a side by a gap. I intentionally did not add
unsupported behavior for those cases.
