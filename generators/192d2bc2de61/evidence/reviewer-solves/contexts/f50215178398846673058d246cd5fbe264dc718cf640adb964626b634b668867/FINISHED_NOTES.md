# Solve notes — exposed post-repair episode

I had already seen and repaired this task's generator before this solve phase, so
this is **not blind**. I did not consult the Racket rule, reference solution, or
private query labels during the solve phase.

From the three visible demonstrations:

1. Read every nonzero cell in row 0 from left to right. Zero gaps are spacing,
   not the end of the legend.
2. For each legend color, inspect the 4-connected components below row 0.
3. The early singleton cells are decoys. The output uses the uniquely largest
   component of that color.
4. Crop each selected component to its tight bounding box, preserving interior
   zeros and its original color.
5. Pack those crops horizontally in legend order with one all-zero separator
   column. Align crop tops; output height is the maximum crop height.

Checks against the visible examples:

- Example 0 legend is 5,3,1 although the large body objects occur 1,5,3 from
  left to right; the output follows 5,3,1. This rejects body-spatial order.
- Examples 0–2 each place small same-color cells above the main objects; choosing
  the first component would return one-cell crops, so size selection is needed.
- Examples 1 and 2 have leading/interior zeros in row 0, confirming that all
  nonzero row-0 cells—not a contiguous prefix—form the legend.

The implementation uses deterministic tie-breaking by size, then top row, then
left column. Visible examples have a unique largest component, so the tie-break
does not affect them.
