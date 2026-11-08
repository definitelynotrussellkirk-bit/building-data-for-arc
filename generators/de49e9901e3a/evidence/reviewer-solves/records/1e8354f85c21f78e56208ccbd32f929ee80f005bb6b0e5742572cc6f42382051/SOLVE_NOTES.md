# Post-repair visible-only solve notes

The labeled examples consistently preserve each nonzero object's color and grid
size while filling every missing cell in that object's tight rectangle. I treat
objects as monochrome 4-connected components rather than grouping globally by
color: query 1 contains two separated color-9 objects, which should be completed
independently. The staircase-shaped objects are important because they rule out
an interpretation limited to L/T/cross shapes. Background remains zero.

Implemented hypothesis: find every nonzero monochrome 4-connected component,
compute its minimum/maximum row and column, and paint that entire rectangle in
the component color. Distinct components are separated in the visible data, so
rectangle collisions are not an observed ambiguity.
