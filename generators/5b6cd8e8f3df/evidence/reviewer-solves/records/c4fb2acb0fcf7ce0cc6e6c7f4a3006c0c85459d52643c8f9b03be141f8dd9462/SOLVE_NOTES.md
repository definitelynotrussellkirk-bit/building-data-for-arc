# Solve work log

## Exposure declaration

Before this solve I had not opened the task's generator, Racket rule, canonical
record, reference solutions, private query labels, audit evidence, or earlier
solution notes. I used only the visible examples printed by `review.py blind
prepare` and the packet's public solve README.

## Observations and hypothesis

Each input contains isolated nonzero single cells on a zero background. In every
training output, each nonzero cell keeps its color and becomes a five-cell
orthogonal plus: the center plus its immediate up, down, left, and right
neighbors. Grid dimensions and background stay unchanged. Examples 0 and 1
show the same operation for repeated and distinct colors; example 2 shows four
colors and confirms that the operation is applied independently to every
nonzero cell.

The visible instances keep centers at least one cell from the border and their
pluses do not conflict. I will still use bounds checks so the inferred operation
has defined behavior at an edge. If two expansions ever overlap, later writes
would only matter when colors differ; the visible data does not identify a
priority rule, so I make no stronger claim.

## Probe 0 — harness red check

Before implementing the rule, I ran the checker against the supplied
`NotImplementedError` template as a deliberate diagnostic probe. Expected
result: execution failure, proving that the checker exercises `solve(grid)` and
that a later green result is attributable to the implementation rather than an
inert test path.

## Revision 1 — orthogonal-plus expansion

Implemented the smallest rule consistent with all visible pairs: copy the grid,
scan original nonzero cells, and write the same color at the center and four
orthogonal neighbors. Writes are based on the original grid, so newly painted
cells do not recursively expand. Added bounds checks without changing any
visible case.
