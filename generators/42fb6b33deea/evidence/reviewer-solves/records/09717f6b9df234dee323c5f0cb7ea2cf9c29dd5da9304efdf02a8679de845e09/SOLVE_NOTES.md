# Solve work log

## Exposure declaration

I had examined this task's generator and executable rule earlier in the repair assignment, so this is **not** an independent blind solve. During this solve episode I kept those sources closed and used only the materialized visible examples in `challenge.json`. The finish declaration therefore records `earlier-exposure=yes` and `reference-consulted=no`.

## Visible-example inference

All outputs are fresh zero canvases with selected colored bounding boxes filled. The selection criterion is the count of the color in the input:

- In training example 0, colors 4 and 9 each occur four times and both bounding boxes are filled, even though color 4's four cells are not all literal corners.
- In training example 1, color 3 occurs four times and is filled; color 1 occurs three times and disappears.
- In training example 2, colors 1 and 5 occur four times and are filled; the five-cell color 2 and three-cell color 7 disappear.

Hypothesis: independently for each nonzero color, fill its complete axis-aligned bounding box if and only if the color occurs exactly four times; erase every other color. The output retains the input dimensions and starts from zeros.

## Implementation and uncertainty

`solution.py` groups nonzero cells by color, creates a zero grid, and fills the min/max row-column rectangle for each group of length four. This directly covers the non-corner four-cell witness visible in training example 0, so the weaker “four literal corners” hypothesis is rejected by the examples themselves. Remaining uncertainty is limited to private queries, whose labels are intentionally withheld.
