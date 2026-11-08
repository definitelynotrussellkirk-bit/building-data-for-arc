# Post-repair visible-only solve notes

## Visible-example hypothesis

Each nonzero color except 8 occurs twice and defines a diagonal endpoint pair.
Color 8 is a fixed wall.  Process pair colors by the row-major position where
each color first appears.

For a pair `(r1,c1)`, `(r2,c2)`:

1. Form the horizontal-then-vertical L: traverse row `r1` to `c2`, then column
   `c2` to `r2`.
2. If every cell on that path is either an endpoint or zero in the **original
   input**, choose it.
3. Otherwise choose the vertical-then-horizontal L.  The visible examples show
   this is a fallback rather than a second clear-path test: the first/third
   examples' earliest color has a wall on each candidate, yet the output still
   draws the vertical route around and up to that wall.
4. Paint the chosen path in the pair's own color while preserving any 8 cell.
   Apply pairs sequentially so later row-major colors overwrite earlier path
   colors at intersections.

This accounts for the three recurring roles in every demonstration: a
both-clear pair (horizontal preference), an H-blocked/V-clear pair, and an
H-and-V-blocked fallback pair.  It also accounts for intersections and fixed
walls.  I am implementing this directly without opening the generator, Racket
source, retained reference solution, or private query labels during this solve.
