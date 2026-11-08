# Solve work log

## Exposure declaration before solving

I had already inspected this task's generator and executable rule during the required repair phase, so this is an **exposed post-repair solve**, not a blind solve. During this solve phase I consulted only `solve/challenge.json`, the local solution file, and the visible check result; I did not reopen the generator, Racket source, canonical reference, or private labels.

## Revision 1 — bounding-box completion per same-color component

Visible-example observations:

- Every nonzero same-color 4-connected component defines a rectangular bounding box.
- The output is blank outside those boxes.
- Each box gets a complete border in the component color, even when the input is a cross or an open three-sided shape.
- Strict interior cells form a local checkerboard: the interior top-left is colored, then colors alternate by row and column.
- Multiple colors are handled independently. The second training example shows two components whose boxes are completed separately.

Implementation hypothesis: find every same-color 4-connected component, compute its bounding box, and paint a fresh zero grid with the full border plus cells of even local interior parity. I chose component-based segmentation rather than grouping all nonzero cells because the visible two-color example requires independent colors and boxes.

Remaining uncertainty before checking: none material for the visible examples. A hypothetical grid with multiple disconnected components of the same color should still be handled separately because connectivity, rather than color alone, is the visible object cue.
