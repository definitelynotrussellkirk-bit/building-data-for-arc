# Solve notes — 297c05190f7c

This is a human work log based on `solve/challenge.json`. I had already seen the
generator rule during the required generator-review phase, so this is **not a
blind solve**. During the solve phase I did not reopen the generator, Racket
source, reference outputs, or private labels.

## Visible-example hypothesis

Each nonzero same-color 4-connected component is handled independently. Replace
that component by its tight axis-aligned bounding rectangle, preserving its
color and leaving all other cells zero.

Visible evidence:

- Train 1 fills the missing cells in each color-1 and color-3 rectangle.
- Train 2 is the connectivity discriminator: the lower color-2 singleton is
  only diagonally adjacent to the other color-2 shape. It remains a singleton,
  while the 4-connected shape above it is completed to a 2x2 rectangle.
- Train 3 has two separated color-6 components. Each becomes its own 2x2
  rectangle rather than creating one global rectangle for color 6. The larger
  color-4 component becomes its own 4x4 rectangle.

## Implementation

Scan row-major, flood-fill each nonzero 4-connected same-color component, find
its minimum and maximum row/column, and paint that rectangle into a fresh
zero-filled output. No alternate revision was needed because the three visible
examples jointly disambiguate per-component versus per-color grouping and
4-connectivity versus diagonal connectivity.
