# Solve notes — final-source visible episode

## Observations from the three demonstrations

- Each input has exactly one complete gray (`5`) guide: a column in demonstrations 1 and 3, and a row in demonstration 2.
- The nonzero color at the top-left is the selected color. Only that color creates new cells. Existing cells, including distractors, remain.
- Demonstration 1: selected-color `8` cells left of column 5 are copied to their equal-distance positions on the right. For example `(3,2)` creates `(3,8)` and `(4,1)` creates `(4,9)`.
- Demonstration 2 establishes both horizontal reflection and the selector exception. The selected `1` cells below row 4 create mirrors above it. The top-left selector at `(0,0)` is not mirrored to `(8,0)`, even though that coordinate is in bounds.
- Demonstration 3 establishes that the source need not lie on the selector's side. Selected `6` cells right of column 5 create left-side mirrors, so a one-way “copy left to right” rule is false.
- A source whose mirror would be outside the grid produces no new cell; the source itself is never erased.

## Hypothesis implemented

Let `T = input[0][0]`. Find the full row or column of gray cells. For every cell of color `T` except `(0,0)`, paint its geometric mirror across that guide if the mirror is in bounds. Preserve everything else.

## Stopping reason

One implementation covers both orientations, both source sides, selector exclusion, and clipping. It passed all three visible demonstrations on the first check, so no additional revision was justified.

No generator source, Racket authority, private labels, or prior solve record was consulted during this episode. Earlier exposure is declared `yes` because I had examined the rule while repairing the generator before starting this visible-only solve.
