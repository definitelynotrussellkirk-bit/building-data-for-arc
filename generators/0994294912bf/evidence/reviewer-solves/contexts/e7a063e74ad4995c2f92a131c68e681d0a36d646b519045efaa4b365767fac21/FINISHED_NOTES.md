# Blind solve work log — 0994294912bf

## Exposure declaration

Before the blind episode was prepared I inspected only packet-level procedural files
(`WELCOME.md`, `repo/AGENTS.md`, and part of `RETURN-GUIDE.md`) while locating the
assignment. I did **not** inspect this task's generator, Racket rule, canonical record,
private labels, prior solutions, or task-specific review material.

## Visible-example observations

The all-9 row and all-9 column divide each grid into four aligned panels. The top
pair demonstrates the operation: a filled object in the upper-left is represented by
only its 4-neighbour boundary in the upper-right, at the same panel-relative cells.

The lower-left supplies the object to transform. The result is overlaid in the
lower-right at matching panel-relative coordinates and clipped by that panel's size.
Pre-existing lower-right cells outside the copied boundary remain unchanged; cells on
the copied boundary are overwritten.

The output color is the color of the top-leftmost occupied source cell. This explains
both uniform sources and the examples where a single corner cell has a different color
from the remainder of the source object. Interior source cells are not copied. Sparse
or one-cell-thick source shapes are already all boundary, explaining the clipped L-shape
examples.

## Hypothesis / implementation

1. Find the separator row and column whose cells are all 9.
2. Extract the lower-left panel and its nonzero occupancy mask.
3. Choose the color at the lexicographically first occupied cell.
4. Mark each occupied cell as boundary when at least one orthogonal neighbour is outside
   the occupied mask (including outside the panel).
5. Overlay those boundary cells into the lower-right panel at identical local
   coordinates, clipping to the lower-right dimensions.
6. Leave every other input cell unchanged.

This predicts query 0 as a 3×3 color-7 outline in the lower-right. It predicts query 1
as a 3×3 color-1 outline beginning at local lower-panel coordinate (4, 2), overwriting
the existing target cell on that outline while preserving the farther color-3 cell.
