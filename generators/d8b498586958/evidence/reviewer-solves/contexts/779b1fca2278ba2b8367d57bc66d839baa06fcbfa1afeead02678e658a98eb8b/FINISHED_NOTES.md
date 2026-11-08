# Visible-only solve work log

This is a human work log, not a token trace. I had already inspected the assigned
generator and canonical rule before this mandatory post-repair episode, so this
solve is **exposed** and will declare `earlier-exposure yes`. I did not consult a
reference solution, private labels, the generator source, or the Racket rule after
`solve_episode.py prepare`.

## Hypothesis from the four visible demonstrations

Every input has a two-row header with one color-5 corner marker, a full color-9
separator, a square color-2 panel A, another separator, and a same-size panel B.
The output is the selected occupancy support recolored 8:

- top-left marker: union of A and B;
- top-right marker: intersection;
- bottom-left marker: symmetric difference / XOR;
- bottom-right marker: A minus B.

The demonstrations include each corner exactly once. I checked the top-right
example cell-by-cell as intersection, the bottom-left example as XOR, the
bottom-right example as A-only, and the top-left example as union.

## Implementation

`solution.py` finds the two full color-9 divider rows, validates square panels,
reads the marker corner, performs the corresponding set operation, and renders
color 8. No hard-coded panel size or operand color is needed.

## Predicted tests

Test 0 is top-right/intersection. Predicted support (zero-based): `(1,2)` and
`(2,3)` in a 5x5 output.

Test 1 is bottom-left/XOR. Predicted support in a 6x6 output:
`(0,3)`, `(0,5)`, `(1,2)`, `(3,2)`, `(3,5)`, `(4,2)`, `(5,0)`.
