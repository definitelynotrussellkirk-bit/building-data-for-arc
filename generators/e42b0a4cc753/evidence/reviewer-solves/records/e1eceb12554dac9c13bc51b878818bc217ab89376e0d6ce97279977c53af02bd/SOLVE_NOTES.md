# Solve work log

## Exposure

Before this solve I had not opened task `e42b0a4cc753`'s generator, Racket rule,
reference solution, private query labels, audit records, or earlier solution
notes. I used only the visible examples produced by `review.py blind prepare`.

## Revision 1 — Manhattan Voronoi fill with stable ties

The non-8 colors are isolated seeds inside a rectangular 8 frame. Every output
keeps the frame and replaces each interior zero with a seed color. I compared
possible rectangular/ray expansion with nearest-seed assignment. Manhattan
nearest-seed regions exactly reproduce all three demonstrations:

- In train 0, the two diagonal-adjacent seeds make the lower-right quadrant
  strictly closer to color 3; the equality line stays color 7.
- In train 2, the same geometry gives color 2 only below-and-left of its seed;
  all ties stay color 1.
- In train 1, cells equidistant from colors 7, 6, and/or 3 use color 6, which is
  the first seed in row-major order. This same stable tie rule explains the
  earlier two examples because their preferred tie color is also first.

I therefore implemented: find the monochrome frame color from the top-left;
collect all interior nonzero, non-frame cells in row-major order; for each zero,
copy the color of the minimum Manhattan-distance seed. Python's stable `min`
keeps the first seed on ties. Original seeds and all nonzero frame cells remain
unchanged. A local visible-example regression first failed on the starter
`NotImplementedError`, then passed after this implementation.

Remaining uncertainty: the visible tasks all use background 0 and a uniform
frame whose color equals the top-left cell. The implementation intentionally
matches that demonstrated contract rather than guessing at unrelated frameless
variants.
