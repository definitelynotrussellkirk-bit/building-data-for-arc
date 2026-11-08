# Post-repair visible-only solve notes

This is a human work log, not a captured model trace. I had earlier exposure to
the task rule while repairing the generator, so this solve is **not blind**. I
did not consult the Racket source, generator implementation, private labels, or
reference solutions during this solve episode.

## Visible evidence

- Each input has three isolated, single-colour objects.
- In every training example, two objects have the same shape after translation,
  while the third object has a different shape.
- The output is the repeated shape's tight bounding-box crop, with occupied
  cells recoloured to 8 and background retained as 0.
- Colour cannot be the selector: the repeated objects use different colours
  across the examples, and colour 2 is a decoy in training example 2.
- Position cannot be the selector: the repeated shape appears in different
  row/column locations.

## Hypothesis

Split nonzero cells into 4-connected same-colour components, normalize each
component by subtracting its minimum row and column, select the unique most
frequent normalized shape, crop its first row-major occurrence to its bounding
box, and recolour occupied cells 8.

The two visible queries each contain one 3-cell decoy and two matching 5-cell
objects, so the same procedure is directly applicable. I am submitting this
single evidence-supported implementation without manufacturing an artificial
failure.
