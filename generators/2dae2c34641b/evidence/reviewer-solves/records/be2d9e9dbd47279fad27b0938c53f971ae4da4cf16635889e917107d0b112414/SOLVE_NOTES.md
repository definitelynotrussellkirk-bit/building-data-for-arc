# Solve notes

## Visible-example observations

Each nonzero color occurs at exactly two cells. In every demonstration, the two cells are connected by an L-shaped path of their own color. The path is directional: choose the endpoint in the smaller row, extend vertically down in that endpoint's column until the row of the lower endpoint, then extend horizontally on the lower endpoint's row until reaching it. This explains both left-turning and right-turning examples and all three colors in the third demonstration.

A horizontal-first alternative is contradicted by every demonstration: for example, the color 2 pair in the first demonstration fills column 5 downward first and only then fills row 5 leftward.

## Implementation

The solver collects each nonzero color's two coordinates, sorts them by row, paints the inclusive vertical segment from the upper endpoint to the lower row, then paints the inclusive horizontal segment to the lower endpoint. It starts from a zero grid so only the intended paths remain.

## Predictions

The same construction is applied independently to every color in both query grids. No reference implementation, generator source, private label, or Racket rule was consulted during this solve phase. I had earlier rule exposure from the generator-review phase, so this is an exposed fresh solve rather than a blind solve.
