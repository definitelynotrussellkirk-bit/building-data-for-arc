# Solve work log

## Exposure declaration

This exact blind task ID was encountered and solved in an earlier interrupted tool session. I did not consult its generator, canonical rule, private labels, or reference solution in either session. The prior visible-example analysis found the rule below, so this is honest earlier task exposure rather than a newly blind inference.

## Rule used

Recolor each four-connected color-1 component that is exactly three cells of a 2×2 box. The output color is determined by the box corner that is missing:

- bottom-right → 2
- bottom-left → 3
- top-right → 4
- top-left → 8

All other components, including non-1 L triominoes and color-1 objects of other shapes or sizes, remain unchanged. The new five demonstrations again exhibit all four orientations and negative objects, and the same component-based implementation should cover both masked queries.
