# Solve notes — b3bfd59c2c43

This is a human work log based only on `solve/challenge.json` during the solve
episode. I had already inspected the task rule while repairing its generator, so
this is explicitly an exposed post-repair solve rather than a blind solve.

## Hypothesis

Across the three visible demonstrations, each nonzero occupied region keeps its
shape and canvas position. Cells on the region's outer cardinal layer become
color 8, while cells surrounded on all four cardinal sides by occupied cells
retain their original color.

The third demonstration is decisive: one connected component contains both 7
and 4. The internal color interface is *not* treated as an object edge; only the
boundary of the combined nonzero occupancy component is recolored. The second
demonstration also shows that cells along the left canvas edge count as exposed
to off-grid space and therefore become 8.

## Implementation

1. Find each 4-connected component of all nonzero cells, ignoring color changes
   inside a component.
2. For each component cell, inspect the four cardinal neighbors.
3. Recolor it to 8 if any neighbor is outside the grid or outside that component.
4. Copy all interior cells and background cells unchanged.

No diagonal connectivity or repeated onion peeling is used; only depth one is
recolored.
