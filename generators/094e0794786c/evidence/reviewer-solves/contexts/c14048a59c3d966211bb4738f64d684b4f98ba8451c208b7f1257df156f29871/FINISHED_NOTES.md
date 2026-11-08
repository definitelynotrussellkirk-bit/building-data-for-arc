# Solve work log

## Prior exposure declaration

Before this visible-only solve I had already reviewed this task's generator and canonical rule while repairing it, so earlier rule exposure is **yes**. During this solve I did **not** reopen or consult the generator, Racket rule, reference solutions, private labels, or earlier solution explanations. The work below uses only the prepared visible examples.

## Revision 1 — normalized symmetric difference

All three visible examples contain one blue object and one red object far apart in the input, while the output is much smaller. Cropping each color to its own tight bounding box and aligning both crops at their top-left corner explains the output dimensions. The output marks cells occupied by exactly one normalized object with color 8:

- Example 1 distinguishes XOR from union because the aligned overlap is zero in the output.
- Examples 0 and 2 show that exclusive cells from both colors survive.
- The output dimensions are the maximum normalized height and width of the two objects, not either original global bounding box.

I implemented that rule directly. Empty symmetric difference is handled as a 1×1 zero grid, although the visible examples do not exercise it. Remaining uncertainty before checking: none among the obvious union/intersection/one-shape alternatives; all are visibly refuted.
