# Solve work log

## Exposure declaration before solving

I had not opened the blind task's generator, canonical rule, prior solutions, private labels, or audit material. I used only `solve-blind/challenge.json` and local reasoning.

## Revision 1

**Observed pattern.** Every input contains (a) one connected multi-cell object in color 1, (b) a single orange (`7`) marker, and (c) one additional singleton whose color is one of `2, 3, 4, 6`. The output clears the grid, copies the color-1 object's normalized shape to the orange marker, and recolors it azure (`8`). The orange cell is the top-left coordinate of the copied shape's bounding box.

**Rotation hypothesis.** The four non-orange code colors form an ordered four-way rotation code: `2 -> 0`, `3 -> 90° clockwise`, `4 -> 180°`, `6 -> 270° clockwise`. This exactly explains all four demonstrations: the triangle is unchanged for 2, the T rotates clockwise for 3, the trapezoid flips for 4, and the five-cell shape rotates counterclockwise for 6.

**Implementation.** Extract all color-1 coordinates, normalize them to their bounding box, rotate the coordinate set the coded number of quarter-turns, then stamp it in color 8 with its normalized `(0,0)` aligned to the orange marker. Return an otherwise-zero grid of the original dimensions.

**Remaining uncertainty.** The demonstrations do not independently prove that these particular colors always carry the same absolute rotation mapping rather than some geometric relation among the markers, but the exact four-code progression and all examples strongly favor the code interpretation.
