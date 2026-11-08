# Solve notes

## Revision 1 — intended solve

Visible examples preserve grid dimensions, row positions, colors, cell counts, and each object's internal geometry. Each nonzero monochromatic 4-connected object is translated horizontally by its own minimum occupied column, so its bounding box touches the left border (column 0). Blank rows and relative vertical placement are unchanged.

Implementation: enumerate monochromatic 4-connected components, compute each component's minimum column, and copy its cells to `(row, column - minimum_column)` in a zero-filled grid of the same shape.

The two queries contain irregular objects, which rules out replacing objects with filled bounding rectangles. I stopped after one implementation because it exactly reproduces all three visible examples and handles each component independently.

Exposure declaration: I had already seen the intended rule while reviewing the generator, so this is an exposed post-repair solve. I did not consult the Racket rule, generator source, private labels, or reference solution during this solve phase.
