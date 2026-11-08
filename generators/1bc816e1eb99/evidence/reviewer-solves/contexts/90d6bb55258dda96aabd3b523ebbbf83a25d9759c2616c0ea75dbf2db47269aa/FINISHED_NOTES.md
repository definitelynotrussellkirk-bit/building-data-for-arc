# Solve notes

## Visible-pattern hypothesis

The grid geometry is unchanged; only yellow (4) components are recolored. Across all four demonstrations, a component that encloses background cells becomes cyan (8), while a component with no enclosed background becomes red (2).

This is not a size rule: the demonstrations contain large solid components colored red and smaller hollow frames colored cyan. It is not simply “non-rectangular means cyan”: the notched/concave component in the second demonstration is red because its missing boundary cell connects the indentation to the exterior.

## Implementation

1. Find each 4-connected yellow component.
2. Restrict attention to its bounding box.
3. Flood empty bounding-box cells reachable from the bounding-box boundary.
4. Any remaining empty cell is enclosed by that component.
5. Recolor the full component to 8 when an enclosed region exists, otherwise to 2.

The implementation preserves all non-yellow cells and supports components touching the outer grid boundary because enclosure is evaluated relative to each component's bounding box.
