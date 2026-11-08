# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, notes, private labels, or any prior solution. I used only `solve-blind/challenge.json` and local Python experiments.

## Observations and hypothesis

The value `8` forms walls. Every other nonzero color occurs exactly twice. In each training output, the two cells of a color are joined by a four-neighbor path of that same color, while the walls stay fixed. The path is shortest among routes through non-8 cells. Simple pairs use an L-shaped route; the third example detours through openings in the walls.

Hypothesis: for each color other than 0 and 8, find a shortest four-neighbor path between its two markers without crossing 8 or a marker of another color, then paint that path with the pair's color.

## Probes

I enumerated all 24 fixed neighbor orders for breadth-first search and compared generated outputs against all three visible training outputs. Five orders with lexicographically ordered endpoints matched every example. They all produce the same paths on both hidden-query inputs, so the remaining tie-break ambiguity does not affect these two queries. I selected the conventional `up, down, left, right` order.

Before implementation, an executable visible-example test against the prepared `NotImplementedError` stub failed as expected; the failure is retained at `checks/blind-tdd-red.log`.

## Remaining uncertainty

The visible examples do not establish behavior for malformed instances with a color appearing other than twice, or for intersecting equal-length routes. The solver conservatively leaves non-pairs unchanged and prevents a path from crossing another color's marker.
