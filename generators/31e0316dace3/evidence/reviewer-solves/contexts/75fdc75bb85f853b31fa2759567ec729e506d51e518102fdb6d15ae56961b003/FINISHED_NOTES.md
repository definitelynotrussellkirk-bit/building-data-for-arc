# Solve work log

I had no earlier exposure to this task's generator, Racket rule, reference
solution, private labels, or earlier solution explanation before preparation.
I used only the visible examples printed by `review.py blind prepare`.

## Revision 1 — expected red check

The supplied `solution.py` still raised `NotImplementedError`. I ran the check
once to establish the expected failing baseline. It reported an execution error
and 0/3 visible examples passed.

## Revision 2 — spatial quadrant compression

Across all three training pairs, each nonzero color denotes one sparse object.
The output is a 2×2 summary of object position: upper-left, upper-right,
lower-left, and lower-right. A quadrant with no colored object is 0. Shape and
cell count do not otherwise affect the output. This explains the absent
upper-left cell in example 1 and absent upper-right cell in example 2.

The implementation groups all cells by nonzero color, computes each color's
centroid, maps that centroid against the input's horizontal and vertical
midlines, and writes the color into the corresponding output cell. The visible
query predictions are `[[6, 7], [0, 1]]` and `[[6, 8], [3, 0]]`.

Remaining uncertainty: the visible data never place two colors in one quadrant
or an object across a midline. The deterministic fallback selects the larger
object if such an ambiguous input occurs; this is defensive behavior, not an
inferred part of the task rule.
