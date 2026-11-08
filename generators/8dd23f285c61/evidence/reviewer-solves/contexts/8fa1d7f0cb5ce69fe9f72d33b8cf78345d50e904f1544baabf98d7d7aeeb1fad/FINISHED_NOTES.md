# Solve notes — 8dd23f285c61

This is a human work log from the visible examples only. I had earlier rule
exposure during generator review, so this is not a blind solve; I did not reopen
or consult the generator, Racket source, private labels, or prior solution files
while solving this episode.

## Hypothesis 1

Color `2` cells are emitters. In the output every emitter becomes `8` and paints
`8` along its full row and column. A ray stops immediately before the first
color-`5` wall cell and otherwise continues to the grid edge. Wall cells stay
`5`; overlapping rays union naturally. The examples show small and large wall
components behaving the same way, so blocking is cell-based rather than based on
component size or orientation.

Implementation plan: collect emitter coordinates from the unchanged input, copy
the grid, set each emitter to `8`, then step in the four orthogonal directions,
painting every non-wall cell `8` until leaving the grid or reaching `5`.
