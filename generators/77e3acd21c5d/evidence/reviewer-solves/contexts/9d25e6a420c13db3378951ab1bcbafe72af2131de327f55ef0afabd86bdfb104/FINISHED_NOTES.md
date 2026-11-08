# Solve work log

## Exposure disclosure

I had already inspected this task's generator and canonical rule while performing the assigned repair, so this is **not** a blind solve. During this post-repair solve I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations. I used only the visible examples emitted by `python3 review.py solve prepare` and my own code.

## Revision 1 hypothesis

The input background is the top-left color. Non-background pixels form separated rectangular objects. Exactly one object is monochrome; its height, width, and color define the output canvas. Among the multicolor rectangles, select the widest one. Its majority color is body and its minority color is the marker.

For each marker pixel, preserve its distance from whichever vertical edge of the selected rectangle is nearer and place it at that distance from the corresponding edge of the output. Do the same independently for the horizontal axis. An exact nearest-edge tie maps to both opposite output edges. Cartesian products handle a two-axis tie. Projected coordinates outside the output are dropped.

Visible evidence:

- Train 0 distinguishes the widest marked rectangle from smaller distractors and shows top/right and bottom/left projection.
- Train 1 contains a vertical midpoint marker that appears at both the top-relative and bottom-relative output rows.
- Train 2 contains a horizontal midpoint marker that appears at both output sides.
- Train 3 combines several markers and a different blank position/size.
- Train 4 repeats the same law under a different palette, arguing against fixed colors or coordinates.

Implementation uses 8-connected foreground components, chooses the unique monochrome component as the blank, chooses the unique widest multicolor component by `max(width)`, and performs the edge-distance projection with tie duplication and clipping.

Remaining uncertainty: the visible family does not show malformed inputs or ties for source width, blank uniqueness, body-color frequency, or multiple marker colors. The solver rejects those cases rather than inventing a tie-break rule.
