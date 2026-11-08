# Solve notes

## Hypothesis 1

Each non-background object is a three-cell L inside a 2×2 bounding box. The missing corner gives an opening direction.

- Gray (`5`) objects create a yellow (`4`) copy shifted one diagonal cell **toward** the missing corner.
- Red (`2`) objects create a green (`3`) copy shifted one diagonal cell **away from** the missing corner.
- Original cells stay in place; projected cells outside the grid are clipped.
- When yellow and green projections collide, green wins. The visible examples support this by requiring the gray projection pass before the red projection pass.

The solver should discover 4-connected red/gray components, recover each 2×2 missing corner, and paint projections in gray-then-red order.
