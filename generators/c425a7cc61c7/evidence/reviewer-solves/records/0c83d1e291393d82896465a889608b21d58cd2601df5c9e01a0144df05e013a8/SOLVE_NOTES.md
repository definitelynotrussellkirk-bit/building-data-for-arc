# Blind solve notes — c425a7cc61c7

## Visible observations

- Every input begins with an isolated nonzero cell at the upper-left corner.
- Elsewhere, one object has the same color as that corner key; other colored
  objects are distractors.
- In all three demonstrations, cropping the keyed object and rotating its binary
  shape 90 degrees clockwise exactly produces the output, retaining the key color.
  Dimensions swap consistently (3x3 stays 3x3; 2x3 becomes 3x2).

## Hypothesis

Treat `grid[0][0]` as a color key. Ignore that one-cell key, crop the remaining
cells of the same color to their bounding box, preserve zeros inside the box, and
rotate the crop 90 degrees clockwise.

## Implementation and edge assumptions

The solution gathers all non-key-marker cells of the keyed color, crops their
bounding box, masks any other color within that box to background, and rotates
without third-party dependencies. The visible tasks contain one keyed object and
an isolated corner marker; behavior for no keyed object is an empty grid.

## Revisions

- Revision 1 (`intent=solve`): direct implementation of the clockwise-rotation
  hypothesis. No prior failed revision was needed.
