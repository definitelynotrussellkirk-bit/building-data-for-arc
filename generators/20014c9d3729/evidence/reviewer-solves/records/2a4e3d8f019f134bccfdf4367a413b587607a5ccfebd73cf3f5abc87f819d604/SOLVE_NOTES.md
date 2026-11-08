# Post-repair solve notes

This is a human visible-example work log. I did not inspect the generator,
reference program, private labels, or prior solution explanations during this
solve phase. I had earlier rule exposure from the generator repair, so this is
an exposed solve rather than a blind solve.

## Hypothesis

Across all three visible pairs, each nonzero color forms one or more separate
4-connected objects. The output preserves exactly the largest object of each
color in place and replaces every smaller same-color object with background 0.
Shapes, positions, and colors are otherwise unchanged. Object size, not bounding
box or an absolute size threshold, explains the examples.

## Implementation

Scan all nonzero cells into exact-color 4-connected components, group components
by color, select the unique largest component in each group, and copy those cells
to an all-zero grid of the same dimensions. A deterministic top-left tie-break is
included only for totality; no visible example contains a tie.
