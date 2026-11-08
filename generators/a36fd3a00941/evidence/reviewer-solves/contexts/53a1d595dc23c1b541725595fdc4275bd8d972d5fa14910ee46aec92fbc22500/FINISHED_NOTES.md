# Solve work log

Earlier exposure before this solve: none to this task's rule, generator, answers, or prior explanations. I used only the visible examples printed by `review.py blind prepare` and the generated challenge files.

## Revision 1 — component packing hypothesis

All three training pairs contain three separated, single-color objects: a 2×2 square near the lower left, a five-cell object near the lower right, and a 1×5 line near the upper left. The output crops the objects to their bounding boxes, preserves each crop exactly (including internal zeros), and places them top-aligned with one zero column between crops. The order is the lower objects from left to right, followed by the upper object. A general ordering consistent with every example is decreasing original bottom edge, breaking ties by original left edge.

I implemented 4-connected same-color component extraction, bounding-box crops, that ordering, and horizontal packing. This predicts query 0's right-hand five-cell object will retain its different orientation rather than being normalized or rotated. Remaining uncertainty: the examples do not distinguish sorting by bottom edge from several equivalent spatial-order descriptions, but the chosen rule is simple and matches all visible evidence.
