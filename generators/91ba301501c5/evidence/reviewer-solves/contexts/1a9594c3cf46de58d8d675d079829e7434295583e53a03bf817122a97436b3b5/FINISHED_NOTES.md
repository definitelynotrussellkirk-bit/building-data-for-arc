# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private labels, audit evidence, or prior solution notes. I used only the visible examples prepared in `solve-blind/` and local Python checks against those examples.

## Revision 1 — vertical rays relative to the divider

The input always contains one complete horizontal row of color 5. Comparing each isolated marker with its output column gives a consistent directional rule:

- Above the divider, color 1 extends upward to the top edge, while color 2 extends downward to the row immediately above the divider.
- Below the divider, color 1 extends downward to the bottom edge, while color 2 extends upward to the row immediately below the divider.

Equivalently, color 1 grows away from the divider and color 2 grows toward it. The divider remains unchanged. Each source marker is included in its ray, and the output has the same shape as the input.

I implemented this directly, with validation for a rectangular grid and exactly one all-5 divider row. I did not find a conflicting visible example. Remaining uncertainty is limited to unseen malformed inputs or additional colors, neither of which the visible task suggests.
