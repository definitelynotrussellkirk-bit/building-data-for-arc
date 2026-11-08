# Solve notes

## Visible-example hypothesis

The first row is a color lookup table. The remaining rows contain separated
4-connected objects made from color `1`. Each whole object is recolored
uniformly, and its new color is selected from the first row at the object's
bounding-box leftmost column.

Evidence from the three visible pairs:

- In pair 1, the bent object spanning columns 2–3 becomes header color 8 from
  column 2, not header color 7 from its topmost/first cell at column 3.
- In pair 2, the four-cell object spanning columns 7–9 becomes header color 3
  from column 7; its cells do not independently copy their own columns.
- Objects of sizes 2, 3, and 4 are all recolored by the same rule.
- The header, zero background, dimensions, and object geometry are unchanged.

## Implementation

Scan body rows, collect each 4-connected color-1 component, compute its minimum
column, read that header cell, and replace every component cell with the selected
color. The code does not infer or extend a cyclic header; it reads the actual
lookup cell shown in the input.
