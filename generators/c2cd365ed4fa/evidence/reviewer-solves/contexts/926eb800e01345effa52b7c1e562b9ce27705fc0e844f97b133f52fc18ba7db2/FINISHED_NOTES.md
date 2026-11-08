# Solve work log

## Exposure declaration

Before this blind solve I had not opened the assigned blind task's generator, Racket
rule, canonical record, private labels, reference solution, earlier solve notes, or
the assigned repair generator. I used only the visible examples in
`solve-blind/README.md` / `challenge.json` and local Python checks.

## Revision 1 — component-count bars

### Observation and hypothesis

Every output has five fixed columns with colors, left to right, `5, 2, 8, 9, 6`.
The background is 7. For each of those colors, the output column is a
bottom-aligned vertical bar. Its height matches the number of 4-connected
components of that color in the input (edge adjacency only); an absent color has
height zero. The output height is the largest of the five component counts.

The demonstrations provide useful cross-checks:

- Train 0 has component counts `[2, 5, 1, 3, 0]`, giving a 5-row output.
- Train 1 has counts `[1, 3, 0, 2, 3]`, giving a 3-row output.
- Train 2 has counts `[1, 0, 3, 4, 2]`, giving a 4-row output.

This also explains why a large connected motif contributes only one unit while
isolated same-color marks each add another unit.

### Probe and red result

I first imported the untouched `solution.py` and asserted its result against every
visible training pair. It failed at the first call with `NotImplementedError`, as
expected, establishing a failing visible-example test before implementation.

### Implementation

I implemented a small breadth-first 4-neighbor component counter, evaluated the
five colors in the observed fixed order, and rendered bottom-aligned bars against
background 7.

### Predicted query summaries

Without consulting hidden labels:

- Query 0 component counts are `[2, 2, 0, 1, 4]`, so the result should be 4×5.
- Query 1 component counts are `[1, 3, 0, 4, 2]`, so the result should be 4×5.

### Alternatives and remaining uncertainty

A superficially similar account is “one unit for the main object plus one for each
isolated noise pixel.” The visible examples make that equivalent because all
non-main components appear to be singletons. Counting connected components is the
simpler invariant and handles multiple multi-cell components consistently. The
fixed color order is directly evidenced by all three outputs, but the visible set
does not explain why this particular order was chosen.
