# Solve notes

## Visible observations

Each input has one connected object in color 2 and one isolated cell in color 1. The output removes both originals and places a color-8 copy at the color-1 cell. The color-1 cell is the top-left corner of the copied object's tight bounding box.

Comparing the first and third training pairs rules out direct copying: the row profile remains in the same vertical order, while each row is reversed within the template's tight bounding box. Thus the object is normalized to its bounding box and reflected left-to-right, not rotated or reflected top-to-bottom.

## Implemented hypothesis

1. Collect all color-2 cells and normalize their coordinates by the template's minimum row and column.
2. Reflect each normalized column `c` to `bbox_width - 1 - c` while leaving the row offset unchanged.
3. Use the unique color-1 cell as the copied bounding box's top-left anchor.
4. Paint the transformed cells in color 8 on a fresh all-zero grid of the original dimensions.

The implementation also clips defensively at the boundary, although all visible examples place the full transformed shape in bounds.
