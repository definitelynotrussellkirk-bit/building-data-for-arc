# Visible-only solve notes

This is a human work log based only on `solve/challenge.json` during the solve phase. I had already seen the task rule while reviewing the generator, so this is **not a blind solve**. I did not consult the Racket source, generator implementation, reference solution, or private labels during this phase.

## Hypothesis from visible differences

Across the four training pairs, every changed cell is an input-zero exactly one cell between two color-4 cells:

- training example 1 shows both a horizontal `4,0,4` and a vertical `4,0,4` becoming `4,4,4`;
- training example 2 shows that two one-cell gaps on one row are both filled, rather than only the first;
- training example 3 preserves the nonzero midpoint `4,9,4`, preserves the `2,0,2` sandwich, and does not bridge wider separations;
- training example 4 again confirms both orientations.

The candidate rule is therefore: copy the grid, then in one simultaneous pass replace a zero by 4 when its immediate left/right neighbors are both 4 or its immediate up/down neighbors are both 4. Read all predicates from the original grid so newly filled cells cannot trigger a second pass.

## Predicted test changes

- Test 1: fill `(1,1)` vertically and `(4,5)` horizontally.
- Test 2: fill `(3,1)` horizontally, plus `(4,6)` and `(6,6)` vertically. Do not bridge the wider gap in column 2 or row 7.

## Revision history

1. Implemented the exact immediate-neighbor, zero-only, two-axis, simultaneous rule. No speculative second rule was added because the visible negative controls already distinguish wider-line completion, arbitrary equal-color completion, blocker overwrite, first-gap-only behavior, and iterative closure.
