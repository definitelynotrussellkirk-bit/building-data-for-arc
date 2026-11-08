# Blind solve notes

Human visible-only work log. I did not open any generator, rule, reference solution,
private label, audit evidence, or repair-task source before finishing this episode.

## Hypothesis

Each nonzero object is evidence for one or more **solid monochrome 3 x 3 blocks**.
The output starts blank and keeps only the four corner cells of every such block.
Overlapping blocks contribute the union of their corners.

This explains the otherwise informative 3 x 4 examples:

- A solid 3 x 4 rectangle contains two overlapping 3 x 3 blocks, so their corner
  union is the full top and bottom rows.
- The irregular 10-cell color-5 object contains only its left 3 x 3 block; the
  one-cell protrusion is therefore erased and the four left-block corners remain.

The implementation enumerates every 3 x 3 window, verifies that all nine cells
share one nonzero color, and paints its four corners into a zero grid of the same
shape. No alternate revision was needed because the irregular visible object
already separates this rule from a simple bounding-box-outline rule.
