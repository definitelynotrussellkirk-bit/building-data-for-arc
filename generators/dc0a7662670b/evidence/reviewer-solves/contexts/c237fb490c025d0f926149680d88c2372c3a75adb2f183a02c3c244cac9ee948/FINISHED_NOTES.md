# Post-repair visible-only solve log

This is a human work log. I had earlier rule exposure while reviewing the assigned generator, so this episode is not blind; during this solve I consulted only `solve/challenge.json` and my own Python code.

## Revision 1

Hypothesis from the four visible demonstrations:

1. Treat each nonzero **same-color 4-connected component** as one object.
2. Compute its exposed-edge perimeter, not its area or bounding-box perimeter.
3. Sort objects by perimeter descending. Training example 4 contains two perimeter-12 objects (colors 7 and 9) and orders color 7 first, so equal perimeters use ascending color.
4. Crop each object to its bounding box, preserve zeros inside the crop, left-align all crops in a common-width output, and put exactly one all-zero row between consecutive crops.

Checks against visible examples by inspection:
- Example 2 separates equal-area shapes by true perimeter.
- Example 3 orders plus (perimeter 12), 2x3 rectangle (10), then 2x2 square (8), refuting area sorting.
- Example 4 exposes the ascending-color tie break.

I implemented this directly with an independent component extractor, perimeter computation, crop, sort, and pack routine. No reference source or private answer was consulted.
