# Solve work log

I had no earlier exposure to this task's generator, Racket rule, reference
solution, private query labels, or prior solution notes. I used only the visible
examples prepared in `solve-blind/`.

## Revision 1 — whole-panel symmetry transfer

The two columns of color 5 split every 5×17 input into three 5×5 panels. The
first two panels contain the same occupied shape and demonstrate a transformation
of the *whole 5×5 coordinate frame*, not merely a tight bounding-box transform.
The output is the third panel under that same transformation.

Visible checks by coordinates:

- Example 0: panel 1 rotated 90° clockwise equals panel 2; rotating panel 3 the
  same way gives the shown output.
- Example 1: panel 1 rotated 180° equals panel 2; the same 180° rotation gives
  the shown output.
- Example 2: panel 1 again rotates 90° clockwise to panel 2; applying it to the
  color-9 panel gives the shown output.
- Query 0 demonstrates a top/bottom reflection.
- Query 1 demonstrates a left/right reflection.

I implemented all eight symmetries of a square and select the one whose binary
occupancy maps panel 1 to panel 2. Occupancy rather than foreground color carries
the rule, while the third panel's actual colors are preserved in the output. If
a symmetric teaching shape admits multiple transformations, the implementation
accepts it only when all matching transforms predict the same result; otherwise
it reports ambiguity instead of silently guessing.

Before implementation, an automated visible-example test failed at the provided
`NotImplementedError`, confirming the test exercised the missing behavior. The
next step is the official visible-only checker.
