# Solve notes — b5af3d6b3cd5

## Visible observations

- Color 5 never changes and forms closed frames plus full divider rows/columns.
- Every other colored cell keeps both its color and its column.
- Within each wall-bounded room, colored cells move downward until they occupy the lowest available cells of their own column.
- When a column contains two colors, their top-to-bottom order is preserved. Train example 1 keeps the `3,6` stack in that order, and train example 2 keeps stacked values rather than sorting them.
- Horizontal wall rows stop motion: upper and lower rooms in the same global column are independent.
- Colors 6 and 8 move exactly like colors 1–4, so the operation is color-agnostic except for wall color 5 and background 0.

## Implementation choice

Find four-connected components of cells that are not color 5. For each component and each represented column, read nonzero values from top to bottom, clear the room cells in the output, and write those values into the bottommost room cells in the same order. Initialize the output with walls copied and all non-wall cells zero.

## Alternatives rejected from visible examples

- Move objects to the bottom of the whole grid: contradicted by interior horizontal walls.
- Pack all markers across a room without respecting columns: contradicted by unchanged marker columns.
- Sort colors while falling: contradicted by multi-marker columns.
- Move only canonical colors 1–4: contradicted by moving colors 6 and 8.
