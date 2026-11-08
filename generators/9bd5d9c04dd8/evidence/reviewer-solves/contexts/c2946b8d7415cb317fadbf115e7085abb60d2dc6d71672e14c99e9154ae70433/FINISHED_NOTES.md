# Visible-only solve notes

## Hypothesis

The nonzero cells form two to four isolated, fully occupied 3×3 tiles.  Color
0 is background; color 1 is the distinguished scoring color; the other
nonzero color is filler.  Return the tile containing the greatest number of
color-1 cells.  The three training outputs are exactly the 9-, 7-, and 6-one
tiles respectively.

I implement this without assuming fixed canvas dimensions or filler color:
find 4-connected nonzero components, keep components that are filled 3×3
rectangles, score them by their count of 1, and return the maximum.  Using
4-connectivity keeps diagonally touching tiles separate.  For an unobserved
tie, the solver chooses the first tile in row-major order.

## Query predictions

Query 0 has candidate one-counts 5, 7, and 4, so the predicted output is:

```text
1 1 1
1 1 1
9 1 9
```

Query 1 has candidate one-counts 0, 4, and 7, so the predicted output is:

```text
1 1 1
1 1 9
9 1 1
```

No generator, Racket rule, private label, reference solution, or earlier solve
notes were consulted during this fresh solve.  There was earlier rule exposure
from the required generator-repair phase, which will be recorded at finish.
