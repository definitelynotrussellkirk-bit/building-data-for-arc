# Solve notes — 9bbc588810ae

This is a human work log from the visible examples. I had earlier rule exposure while repairing this generator, so this is an exposed post-repair solve, not a blind claim. During this solve episode I read only `solve/challenge.json` and did not reopen the generator, Racket source, private labels, or prior solution explanations.

## Hypothesis from the three demonstrations

Each input is four 5x5 panels separated by full columns of 9. The last panel is a query shape. The first three panels are candidate prototypes, each in a different color. The output preserves the query's exact cells and replaces its color with the color of the candidate whose cropped shape matches the query after a rotation or reflection.

Evidence:

- Demo 1: the last-panel color-4 shape is congruent up to symmetry to the color-3 source; the output occupies the query cells in color 3.
- Demo 2: the last-panel color-4 shape matches the color-1 source; the output uses color 1.
- Demo 3: the last-panel color-8 shape matches the color-7 source; the output uses color 7.

The colors themselves are labels, not part of the geometric match. Translation inside a panel is irrelevant, so each shape must be normalized to its bounding-box origin before comparison.

## Implementation probe

`solution.py` extracts the four panel-local cell sets, normalizes them, enumerates the eight ordinary rotations/reflections of the query, scans candidate panels left-to-right, and paints the original query coordinates with the first matching source color. This directly predicts all three visible outputs. No fallback heuristic such as area, bounding-box dimensions, or lowest color is used.

## Remaining uncertainty

The visible examples do not explicitly distinguish every symmetry convention or a tie between multiple congruent sources. The generated lesson appears designed to have one geometric match; the implementation follows the natural left-to-right choice if a tie occurs.
