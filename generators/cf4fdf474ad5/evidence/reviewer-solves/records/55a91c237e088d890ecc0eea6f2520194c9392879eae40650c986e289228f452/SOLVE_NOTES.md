# Post-repair visible-example solve log

This is a human work log. I had earlier exposure to the repaired task while reviewing its generator, so this episode is **not blind**. During the solve episode I did not reopen the generator, Racket rule, reference solutions, or private labels.

## Hypothesis

The input contains separated rectangular nonzero patches made from colors 8 and 3. The output is one patch cropped to its bounding box.

Across the three visible examples:

- a 9-row patch can contain more color-3 cells yet is never selected, suggesting a height-at-most-8 eligibility gate;
- among eligible patches, the selected crop has the greatest absolute count of color 3, not the greatest density or largest area;
- example 1 supplies an equal-green-count tie and selects the smaller-area 8×9 patch rather than the earlier 8×11 patch;
- a final top-left tie-break is included for determinism, though the visible examples do not require a second equal-area tie.

Implementation: find 4-connected nonzero components, compute each bounding box and color-3 count, discard components taller than 8, sort by `(-green_count, bbox_area, top_row, left_col)`, and return the selected bounding-box crop.
