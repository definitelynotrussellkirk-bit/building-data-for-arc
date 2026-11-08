# Solve work log

Earlier exposure: none. I did not inspect any generator, Racket rule, reference
solution, private labels, prior solve explanation, or audit evidence before this
solve.

## Hypothesis

The isolated nonzero cell at input coordinate `(0, 0)` names a color. Elsewhere
in the input there are several separated colored objects. Select the object with
the named color, crop its bounding box, and rotate the cropped object 90 degrees
clockwise. Empty cells in the crop remain background color 0.

Checks against the visible demonstrations:

- Example 0: the selected 8-object is `111/110/110`; clockwise rotation is
  `111/111/001`, matching the 3x3 output.
- Example 1: the selected 1-object is `111/010/010`; clockwise rotation is
  `001/111/001`, matching the output.
- Example 2: the selected 3-object is 3x4; clockwise rotation produces the shown
  4x3 output, including the asymmetric last two rows.

I implemented only that rule. The main remaining uncertainty is whether a future
input could contain multiple non-marker components of the selected color; the
visible task consistently provides one selected object, so the solution treats
all non-marker cells of that color as its extent.
