# Solve notes

## Visible-example hypothesis

The two top corners act as a legend. The top-left value is the source color and
the top-right value is the replacement color. Every other occurrence of the
source color changes to the replacement color. Both corner legend cells remain
unchanged. Other colors and zeros remain unchanged.

The examples deliberately include a source-colored cell in row 0 away from the
corners, so “only recolor lower rows” is inconsistent with the visible outputs.
They also contain lower-row source cells, so “only recolor row 0” is inconsistent.

## Implementation

Copy the input, read `source = grid[0][0]` and `target = grid[0][-1]`, then scan
all coordinates. Replace a source-colored cell unless it is one of the two top
corners. This preserves shape and all unrelated cells.

## Exposure declaration context

This is a fresh visible-example implementation, but I had already inspected the
task while repairing its generator. I did not consult the Racket source or any
private query labels during this solve episode, so earlier exposure is `yes` and
reference consultation during the episode is `no`.
