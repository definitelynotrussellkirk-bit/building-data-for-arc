# Blind solve: 4ee97d4d2321

## Exposure and inputs

Before this solve I read only packet-level instructions and the public presentation
produced by `python3 review.py blind prepare`. I have not opened any generator,
canonical rule, task notes, reference solution, audit, or private query labels.
The packet-level ARC design and parametric guidance was opened early; it contains
no task-specific rule information. Earlier exposure to this task's rule: no.

## Hypothesis 1

Every demonstration has exactly one full-height cyan (8) column. Keep the input
and reflect each other nonzero cell across that column: destination column
`2 * divider - source_column`. Clip reflected cells outside the grid. Preserve
already occupied cells; the visible examples contain no contradictory collision.

Evidence: example 0 is 8 x 11 with divider column 3 and left-side shapes appearing
at columns 4 and 5. Example 1 is 9 x 12 with divider column 4, and shapes on the
right copy left. Example 2 is 10 x 11 with divider column 5 and objects on both
sides. Example 3 is 8 x 9 with divider column 5: most color-1 cells would reflect
past column 8, and only the source at (2,2) produces an in-bounds copy at (2,8).
This clipping explains the unequal number of copied cells.

## Implementation and check

Implemented one direct reflection pass on a copy of the original input; newly
painted cells are not fed back into the transformation. The solution deliberately
requires the vertical cyan divider observed in the demonstrations. Horizontal
dividers and collisions remain outside the observed evidence.

The public checker is the only reference-dependent operation used. Its masked
query correctness remains withheld; a visible pass will not establish query
correctness. No failed revision has been manufactured.
