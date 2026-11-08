# Visible-only solve notes

## Hypothesis

The examples partition every nonzero color into same-color 4-connected
components. A whole component survives if any of its cells lies on the outer
row or column; otherwise the whole component is replaced by zero.

Evidence from the visible demonstrations:

- Example 0 keeps the color-7 component because it reaches the top border and
  the singleton color 2 because it reaches the right border, while erasing the
  interior color-9 component.
- Example 1 is the critical color-role check: two disconnected color-4
  components have opposite fates. The two-cell component at the left border
  survives, while the interior 2x4 color-4 block is erased. Therefore the rule
  is component-based, not “keep/erase a color globally.”
- Example 2 keeps the color-4 component touching the top and color-5 component
  touching the right, while erasing the interior color-7 rectangle.

I use cardinal connectivity, not diagonal connectivity, because the objects in
all examples are joined orthogonally and the transformation is expressed per
contiguous object.

## Query predictions used to sanity-check the implementation

- Query 0: erase the interior color-3 pair at row 1 and the interior color-4
  pair; keep the separate color-3 pair touching the right edge, color-7 pair
  touching the left edge, and color-9 pair touching the bottom edge.
- Query 1: keep the top-touching color-7 component and right-edge singleton 1;
  erase the interior color-8 component.

## Implementation

Scan the grid, flood-fill each unseen nonzero same-color component with four
neighbors, record whether any member is on the outer frame, and copy only such
components to an initially zero output of the same dimensions.

This is an exposed post-repair solve: I had seen the task rule during generator
work before preparing this visible-only episode. I did not consult the generator,
Racket source, reference solution, or hidden query labels during this solve.
