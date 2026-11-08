# Exposed post-repair solve: visible-example work log

This is a reviewer-authored work log, not a captured token-level conversation.
Earlier rule exposure: **yes**, during generator repair. Reference consulted
during this solve: **no**. I used the preparation tool's visible examples and
query inputs; the generator, reference source, earlier solution explanations,
and private answers stayed closed during this phase.

## Visible observations and initial hypothesis

The three demonstrations preserve their shapes (14×11, 17×16 and 12×15).
Each has several yellow rectangular outlines, each containing one colored
interior cell. Output zeros inside each outline take that interior color.
In demonstration 0, the upper box fills with 9 and the lower box with 2;
the two exterior 1s and other exterior cells remain. Demonstration 1 uses
different colors for its two boxes, and demonstration 2 preserves outside
colors even where they touch a yellow border. Repeated marker colors in
different boxes receive the same local treatment.

Hypothesis: find each yellow outline independently, identify its interior
marker, fill only its interior zeros with that color, and copy all other
cells. Exterior objects do not choose a box's fill color. This accounts for
all observed changes without selecting a largest or first box.

## Revision 1

Implemented a four-neighbor traversal of yellow cells, a bounding box for
each component, and an interior-color lookup. The solution makes a fresh
copy and writes only blank cells strictly inside each rectangle. It uses
no task library, reference helper, stored labels, or hard-coded output grid.
The query inputs are 13×11 and 12×13; their outputs remain unknown to the
feedback interface. Run the visible-only check next; keep its actual result.

No failed solution revision or intentional teaching negative has been created.
