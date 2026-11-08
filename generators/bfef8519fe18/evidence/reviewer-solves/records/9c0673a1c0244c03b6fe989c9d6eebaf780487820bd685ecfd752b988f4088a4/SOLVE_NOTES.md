# Blind solve work log

## Observation

The color-1 cells form walls and an outer frame.  Every connected region of
non-1 cells in the visible examples contains one nonzero marker color.  The
output preserves the color-1 walls and replaces every cell in each region,
including zeros and the marker itself, with that region's marker color.

This explains all three demonstrations, including irregular regions that are
not simple rectangles in train examples 1 and 2.  Therefore the implementation
uses four-neighbor connected components rather than trying to infer rectangular
row/column partitions.

## Implementation choice

Traverse every four-connected component whose cells are not color 1.  Collect
its colors other than 0 and 1.  When exactly one marker color is present, fill
the component with it.  If a component has no unique marker, leave it unchanged
instead of inventing a color; the visible task domain appears to guarantee one.

## Failed or revised ideas

No substantive failed rule hypothesis was needed.  I initially described the
objects as rectangular compartments, but train examples 1 and 2 show that walls
can create L-shaped/irregular connected regions.  I revised the rule to connected
components before writing the solution.

No generator, canonical rule, private labels, earlier solution explanation, or
reference implementation was consulted during this solve.
