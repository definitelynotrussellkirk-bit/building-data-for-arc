# Solve work log

## Prior exposure

I had not seen task `981730af48bb`, its generator, its Racket rule, private labels,
reference solution, or earlier solution explanations before this blind episode. I
only ran the packet's generic setup and preparation commands and read the visible
examples printed by `solve_episode.py blind prepare`.

## Revision 1 — horizontal midpoint collapse

**Observation.** Every nonempty row contains exactly two cells of one nonzero
color. The output clears both endpoints and places one cell of that same color
halfway between their columns. Examples include columns 4 and 6 becoming 5,
columns 1 and 5 becoming 3, and columns 2 and 6 becoming 4. Empty rows remain
empty and the grid dimensions do not change.

**Hypothesis.** Independently for each row and nonzero color, replace its two
horizontal endpoints by one cell at their integer midpoint.

**Implementation.** Group nonzero columns by color within each row, require two
endpoints and an even separation, and write the color at `(left + right) // 2`
into an otherwise zero grid. The checks are intentional: they avoid silently
inventing behavior outside the visible domain.

**Predicted queries.** Query 0 should place color 2 at `(1,3)`, color 6 at
`(4,3)`, and color 1 at `(5,5)`. Query 1 should place color 3 at `(0,3)` and
color 6 at `(3,1)`.

**Alternatives considered.** Keeping one inner endpoint, filling the interval,
or reusing one row's spacing all disagree with at least one visible example.
There was no failed revision before this one.
