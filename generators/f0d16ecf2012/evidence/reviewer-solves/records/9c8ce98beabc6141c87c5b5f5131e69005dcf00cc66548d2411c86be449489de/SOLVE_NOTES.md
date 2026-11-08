# Solve notes

## Visible-example observations

- Color 9 is unchanged and forms the lane walls.
- Every other color keeps its color, shape, and cell count.
- Colored content moves only east.
- A connected L-shape or bar translates rigidly until its rightmost cell is adjacent to the east wall.
- Diagonally touching same-color cells are not one 4-connected object. In the visible examples, each diagonal singleton docks independently, producing a vertical right-aligned set rather than preserving the diagonal offset.

## Hypotheses considered

1. **Move each whole lane as one shape.** Rejected: the diagonal singleton examples would preserve their relative column offsets, but the shown outputs right-align each singleton independently.
2. **Right-align each occupied row.** Rejected: the asymmetric connected L-shapes preserve their internal offsets; row-wise packing would distort them.
3. **Move each component one step.** Rejected: shown components traverse multiple columns and stop at the wall.
4. **Selected rule:** identify same-color 4-connected components excluding colors 0 and 9; for each component, repeatedly translate one column east while the move stays in bounds and avoids color-9 walls. Components are evaluated independently. Paint the walls and final component positions onto a zero grid.

## Implementation notes

The solver uses row-major 4-neighbor BFS. For each component it keeps a static board of walls plus that component's original cells, matching the visible fact that its own occupied footprint does not block rigid translation. Other colored components are intentionally not blockers.
