# Post-repair visible-only solve notes

I had already inspected the selected generator and canonical rule while repairing it, so this is **not blind**; I will mark earlier exposure `yes`. After `solve prepare`, I used only the displayed examples and did not reopen the generator, Racket rule, prior solution, or hidden labels.

Hypothesis from the visible examples: locate the color-2 and color-3 objects independently, translate each object's bounding-box top-left to `(0,0)`, and overlay their normalized occupied cells. A cell occupied by both becomes 8; red-only remains 2; green-only remains 3; absent cells are 0. The output dimensions are the smallest rectangle containing the union of the two normalized objects.

Checks against the examples:
- Example 0: the red vertical domino normalizes to `(0,0),(1,0)` and the green object overlaps at `(1,0)`, producing one cyan cell and the displayed 3x3 union.
- Example 1: the same red domino overlaps the green object only at its second normalized cell, matching the shown cyan location.
- Example 2: the red horizontal triple overlaps the green object at its middle normalized cell, matching `[2,8,2]` on the first row.

Implementation is direct set normalization and overlay; no orientation changes, input spacing, or filled bounding boxes are preserved.
