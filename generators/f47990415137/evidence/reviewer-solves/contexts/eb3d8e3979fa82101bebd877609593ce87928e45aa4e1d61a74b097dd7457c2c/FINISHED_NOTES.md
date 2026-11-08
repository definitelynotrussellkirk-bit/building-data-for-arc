# Blind solve notes — f47990415137

## Visible pattern analysis

All outputs preserve the background and every nonzero object's occupied cells; only colors change. The output palette is always 2, 3, or 4.

I first compared component areas, but equal-area and unequal-area examples do not support an area-only rule: six-cell components consistently become 2, while three-cell components can become either 3 or 4. The stronger invariant is the axis-aligned bounding box of each 4-connected same-color component:

- height greater than width → color 2;
- width greater than height → color 3;
- equal height and width → color 4.

This explains every visible object, including sparse L-shapes: the 4×6 L becomes 3, the 4×3 L becomes 2, and the 2×2/4×4 L-shapes become 4. It also explains lines, rectangles, and the singleton.

## Implementation

Traverse 4-connected nonzero components without merging diagonal or differently colored objects. Measure each component's inclusive row/column span and recolor its cells according to the three-way aspect comparison. Leave zeros unchanged.

## Test-instance predictions

- Test 1: horizontal 4 and 5 objects → 3; two tall 4 objects → 2; square-bounding-box 1 object → 4.
- Test 2: left vertical 3 and tall 5 objects → 2; upper-right wide 3 object → 3; the large connected 2 object has a 6×6 box → 4.
