# Blind solve notes

## Observations

- Each example contains a monochrome rectangular frame and two singleton-colored cells in its interior.
- The added color is always 9 and is confined to background cells inside the frame.
- In examples 0 and 2, the two markers share a row and are two columns apart. The output fills the intervening column throughout the frame interior.
- Example 1 disambiguates this from a simple midpoint column. Its added cells are exactly those interior cells whose Manhattan distance to marker `(3,6)` equals their Manhattan distance to marker `(7,2)`:
  `(2,2),(3,2),(4,3),(5,4),(6,5),(7,6),(7,7),(7,8),(7,9)`.

## Hypothesis

Copy the grid and recolor every zero-valued interior cell with 9 exactly when it is equidistant in Manhattan (L1) distance from the two singleton markers. Preserve the frame and markers.

## Query expectations

- Query 0 has vertically adjacent markers, so no integer grid cell is equally distant from them; the output should remain unchanged.
- Query 1 has markers two rows apart in the same column; the equidistant set is the interior row midway between them.

## Implementation

Detect the most frequent nonzero color as the frame, use its bounding box as the rectangle, identify the two other nonzero interior cells as markers, and paint the L1 bisector only onto zero cells.
