# Visible-only solve notes

This is a human work log for the prepared post-repair episode. I had earlier rule exposure during generator repair, so this is not a blind record. After `solve prepare`, I used only the displayed examples and did not inspect the generator, Racket source, references, private labels, or prior solve explanations.

## Observations

Each input contains three separated monochrome 4-connected objects: an L tetromino, a 2x2 square, and a singleton. Every output is a 1x3 row containing the three object colors.

The L and square both have area four, so area does not explain their order. Their 4-neighbour perimeters are 10 and 8 respectively; the singleton perimeter is 4. All four demonstrations order colors as L, square, singleton, independent of where the objects appear. This supports sorting by perimeter descending. I use color ascending as a deterministic tie-break, although the visible episode has no perimeter ties.

## Predicted queries

- Query 0: color 9 L (perimeter 10), color 5 square (8), color 2 singleton (4) -> `[9, 5, 2]`.
- Query 1: color 2 L (10), color 1 square (8), color 9 singleton (4) -> `[2, 1, 9]`.

The implementation extracts same-color 4-connected components, computes exposed 4-neighbour edges, sorts by `(-perimeter, color)`, and returns one color row.
