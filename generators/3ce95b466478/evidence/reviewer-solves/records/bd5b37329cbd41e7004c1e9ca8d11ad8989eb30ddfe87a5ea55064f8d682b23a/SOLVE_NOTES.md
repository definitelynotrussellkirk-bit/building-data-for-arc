# Solve notes

This is a human work log from the visible challenge only. I had seen the task rule earlier while repairing the generator, so this is **not a blind solve**; I did not reopen the generator, Racket source, reference solutions, private labels, or prior explanations after `prepare`.

## Visible-example analysis

- Hypothesis 1: ignore the lone non-red colored object (3, 6, or 9) and treat each 4-connected color-2 region as an object.
- Train 1 red-object cell counts are 6, 5, 3, and 2. The output is the 5-cell object, cropped and recolored 8.
- Train 2 counts are 8, 7, 6, and 3. The output is the 7-cell object.
- Train 3 counts are 7, 6, 4, and 2. The output is the 6-cell object.
- Therefore the consistent rule is: rank red components by cell count, select the second-largest, crop its bounding box, recolor its cells 8, and use 0 for holes/background inside the crop.

A perimeter-based ranking was considered because shape compactness varies, but it does not explain the three visible count orderings as directly as second-largest-by-cell-count. The examples have distinct sizes, so tie behavior is not identified by the visible data; the implementation uses top row only as a deterministic fallback.

## Revision 1

Implemented 4-neighbor component extraction, descending size ranking, second-object selection, crop, and recolor. No deliberate negative or diagnostic submission was made.
