# Solve notes

## Visible-example observations

- Outputs keep grid dimensions and almost every cell unchanged.
- Some red (`2`) components become solid green (`3`) 2×2 blocks.
- The changed red components are exactly three connected red cells occupying three corners of a 2×2 bounding box.
- Red straight triominoes, red full 2×2 squares, and red dominos remain red.
- Non-red L shapes remain unchanged.
- In examples where the missing corner already contains a non-red value (for example `5`, `8`, or `9`), that corner is still overwritten with green. Therefore the rule is about the red component's bounding box, not merely filling an empty cell.
- Targets at an edge are transformed normally.

## Hypothesis

For each four-connected red component independently: if it has exactly three cells and its bounding box is exactly 2×2, paint all four cells of that box green. Leave every other component and cell unchanged.

## Implementation

The solver copies the input, flood-fills all color-2 components, checks component size and bounding-box dimensions, then paints qualifying boxes with color 3. The scan reads components from the original input so output painting cannot merge or alter later component detection.
