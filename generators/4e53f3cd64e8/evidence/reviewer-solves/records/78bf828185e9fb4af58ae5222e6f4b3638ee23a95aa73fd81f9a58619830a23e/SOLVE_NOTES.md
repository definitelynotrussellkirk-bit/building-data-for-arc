# Solve work log

## Prior exposure

Before this visible-only episode I had already inspected the selected generator and canonical authority while repairing the task, so this is **not blind**. During this episode I kept those sources closed and used only the displayed examples, challenge data, and visible check feedback.

## Revision 1

Hypothesis from the three visible pairs:

1. Read every nonzero entry of the first row from left to right; zeros are separators, not an instruction to stop.
2. Ignore the all-zero second row. In rows 2 onward, locate the unique 4-connected nonzero component of each legend color.
3. Crop each selected component to its tight bounding box, retaining zeros inside the box.
4. Place the crops left-to-right in legend order, top-aligned, with one zero column between adjacent crops. The output height is the tallest crop and shorter crops are zero-padded below.

Evidence: train 0 orders the body components as 5, 9, 8, 3 despite their spatial positions; train 1 includes color 2 after a zero in the legend and places its vertical crop last; train 2 similarly orders 1, 7, 6 and pads the shorter first two crops to the three-row height of color 6.

Implementation uses a direct 4-neighbor flood fill, tight component crops, and deterministic gallery packing. I did not test competing spatial-order or numeric-color-order rules because all three visible examples already contradict them.
