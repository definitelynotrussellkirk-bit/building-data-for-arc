# 1bfb2ef9ca71

Version `3.1.0`; canonical Racket authority unchanged and pinned by rule hash
`a0ec8172be31`.

A zero-background grid contains two or three colors. Each active color appears
exactly twice at diagonally opposite corners of a separated axis-aligned
rectangle. The output clears the grid and draws each rectangle's hollow border
in its marker color.

Ordinary support uses grids 8..12 rows by 7..14 columns, rectangle sizes 3..5 by
3..6, both diagonal endpoint orientations, and a canonical-weighted profile.
The public exact controls are only `grid_h`, `grid_w`, and `rectangles`; all
joint combinations are constructive and observable.

The three-example production schedule alternates canonical-height and taller
rectangles so that the canonical-fitting “always height three” shortcut is
explicitly refuted. See `notes.md`, task tests, and
`counterexamples/fixed_height_three.json` for the current source-bound evidence.
