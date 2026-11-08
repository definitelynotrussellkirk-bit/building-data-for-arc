# Blind solve notes — 372fcf6aa6ad

## Visible-example observations

- Each input contains four isolated monochrome objects on a zero background.
- Each output contains exactly those objects, with internal pixels preserved after a 90° clockwise rotation.
- Objects are concatenated left-to-right with exactly one zero column between adjacent bounding boxes.
- The output height is the maximum rotated-object height; shorter objects use `floor((H-h)/2)` rows of top padding, so they are vertically centered with any odd extra row below.
- Ordering is ascending painted-cell count. Every visible equal-size tie is resolved by descending color value:
  - train 2: area 8 colors 5 then 1;
  - train 3: area 5 colors 8 then 3;
  - train 4: area 5 colors 6 then 2.

## Hypothesis

Extract 4-connected same-color components, crop them, sort by `(number_of_cells, -color)`, rotate each crop clockwise, vertically center all crops in a common-height strip, and join with one blank column.

## Alternatives rejected from visible examples

- Sorting by input position fails immediately (for example train 1 output starts with the right-side color-2 object).
- Sorting by color alone fails across all examples.
- Sorting by bounding-box area does not explain train 2's color-5/color-1 tie order.
- Packing without rotation fails for the asymmetric color-2 object in train 1 and the asymmetric small objects elsewhere.

## Implementation notes

The solution uses same-color 4-connectivity rather than assuming one component per color. This preserves the visible object concept and avoids accidentally merging diagonally touching shapes.
