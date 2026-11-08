# Post-repair solve notes

## Visible-example hypothesis

For each nonzero color, count all of its input cells.

- When the color occurs **exactly twice** and the two cells share a row, fill the inclusive horizontal segment between them.
- When it occurs exactly twice and the two cells share a column, fill the inclusive vertical segment between them.
- Leave singleton colors, colors occurring three times, and two-cell colors on different rows and columns unchanged.

Evidence from the four visible demonstrations:

- Demo 1 connects a horizontal color-3 pair and a vertical color-1 pair.
- Demo 2 connects horizontal colors 9 and 5 plus vertical color 1, while diagonal color 8 stays unchanged.
- Demo 3 connects horizontal color 8 and vertical color 9, while the three color-2 markers stay unchanged. This rules out connecting the extrema of every aligned color.
- Demo 4 connects two horizontal pairs and a vertical pair, while singleton color 5 stays unchanged.

## Implementation

Collect positions by color, require exactly two positions, and paint only when their row or column coordinate agrees. Work on a copied grid so the input is not mutated.
