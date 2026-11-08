# Blind solve notes — b3bfd59c2c43

## Visible-only hypothesis

Each nonzero monochrome component is a filled shape. The output keeps strictly
four-neighbor-interior cells in the original color and recolors every boundary
cell azure (`8`). A cell is boundary when at least one orthogonal neighbor is
outside the grid or is not the same color. Background (`0`) is unchanged.

Evidence from the visible examples:

- the 4×4 block becomes an azure one-cell frame with a 2×2 original-color core;
- the 5×5 block similarly leaves a 3×3 core;
- cells that only have a diagonal background exposure stay original, so the
  boundary test is orthogonal rather than eight-neighbor;
- thin tips and arms have no four-neighbor interior and therefore become azure.

The first query includes a rectangle touching the top and right grid edges, so
outside-grid neighbors must count as exterior. The second query includes three
separate colors and an irregular shape with an inward notch; the same local rule
handles both without object-specific dimensions.

No generator, rule, reference solution, private label, prior explanation, or
audit evidence was consulted.
