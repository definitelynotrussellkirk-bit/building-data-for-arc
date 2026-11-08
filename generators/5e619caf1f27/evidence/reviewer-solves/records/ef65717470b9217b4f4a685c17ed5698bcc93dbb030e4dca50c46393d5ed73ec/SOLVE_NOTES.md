# Solve notes

## Visible-example hypothesis

Each input has a solid outer nonzero rectangle containing a smaller solid rectangle of a second color. The output preserves both rectangles and paints a rectangular frame outside the outer rectangle using the inner rectangle's color.

The frame width is not fixed:

- Training example 2 is capped at width 1 by the top margin.
- Training examples 1 and 3 use width 3, matching the smaller inner-rectangle dimension while all four outside margins permit it.
- Training example 4 uses width 2, capped by the bottom margin.

Thus the thickness is `min(inner height, inner width, top margin, left margin, bottom margin, right margin)`. The frame occupies the expanded outer bounding box minus the original outer bounding box.

I implemented that rule directly. I did not inspect the Racket source, generator, private labels, or any reference solution during this solve. I had earlier rule exposure from the required generator-review phase, so this is an exposed post-repair solve rather than a blind solve.
