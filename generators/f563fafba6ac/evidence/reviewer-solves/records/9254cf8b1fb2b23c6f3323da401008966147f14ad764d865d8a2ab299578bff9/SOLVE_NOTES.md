# Solve work log

## Prior exposure

Before this post-repair solve I had necessarily inspected and repaired the assigned
generator, so I already knew the intended transformation family.  I did **not**
consult the Racket authority, generator source, reference solutions, private query
labels, or the earlier blind-solve notes while writing this solution.  The program
below is justified independently from the visible examples in `challenge.json`.

## Visible-example observations

All nonzero cells form separated, monochromatic, four-connected objects.  The
outputs preserve every object's exact shape and color, crop away its surrounding
background, top-align the crops, and concatenate them horizontally with one zero
column between adjacent objects.

The ordering evidence is:

- In every example the solid 3×3 object is first.
- One-hole 3×3 rings follow, ordered by increasing color: `5, 7`; `1, 7`;
  and `3, 5`.
- In train example 2, the tall object with two enclosed zero regions follows both
  one-hole rings even though its color is `1`.

That supports the lexicographic key `(number of enclosed background regions,
color)`, rather than input position, area, or color alone.

## Implemented hypothesis

1. Find each nonzero four-connected monochromatic component.
2. Crop it to its bounding box.
3. Count four-connected zero regions inside the crop that do not touch the crop
   boundary; these are the object's enclosed holes.
4. Sort crops by `(hole count, color)`.
5. Top-align and pack them left-to-right with exactly one blank column between
   crops.

The implementation is intentionally general: it does not assume 3-column-wide
objects, fixed grid dimensions, or a fixed number of components.  Remaining
uncertainty is limited to transformations not distinguishable from the three
visible demonstrations; no private-label feedback was used.
