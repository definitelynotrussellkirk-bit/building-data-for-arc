# Post-repair visible-only solve notes

## Exposure declaration

I had already seen the task rule while repairing the assigned generator, so this is not a blind solve. After `solve prepare`, I used only the visible presentation in this solve directory and did not reopen the generator, Racket rule, canonical reference, or private labels.

## Visible evidence and hypothesis

- Train 0 has red (2) objects of 4-connected sizes 2, 3, and 4; the output is `[2, 3, 4]`. The five other nonzero colors are distractors.
- Train 1 has red component sizes 1, 3, 3, and 3; the repeated threes are all retained in the output. This rules out deduplicating sizes.
- Train 2 has red component sizes 1, 1, 2, and 8. The two red singletons at `(1,8)` and `(2,9)` touch only diagonally yet remain separate, so connectivity is orthogonal/4-connected rather than 8-connected.

Hypothesis: find every 4-connected component of color 2, count its cells, sort all counts ascending while preserving multiplicity, and return the counts as one row. Ignore every non-red color.

## Query predictions used as a manual cross-check

- Query 0: red sizes are `1, 1, 2, 2, 9`, summing to the visible red-cell count 15.
- Query 1: red sizes are `1, 3, 4, 5`, summing to the visible red-cell count 13.

The implementation is a direct iterative flood fill, with no dependence on fixed canvas size, palette, component count, or component-shape template.
