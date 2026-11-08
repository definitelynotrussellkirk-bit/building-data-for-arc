# Solve work log

## Exposure declaration

Before this solve episode I had already reviewed this task's generator and Racket authority while repairing it. During this episode I kept those sources closed and used only `solve/challenge.json`, my own Python, and visible-only check feedback.

## Revision 1

The three demonstrations suggest two disconnected masks, colors 1 and 2, are translated independently to their own top-left origins and then combined. The single corner cell is a legend: control 6 gives symmetric difference in demonstration 1, control 3 gives union in demonstration 2, and control 4 gives intersection in demonstration 3. The output is the tight bounding box of the resulting coordinate set, rendered with color 8.

I checked this interpretation manually against every visible pair:

- In demo 1, the normalized 1-mask is a two-cell horizontal domino and the 2-mask is a 3-by-2-ish block; their XOR exactly gives the shown three color-8 cells.
- In demo 2, union preserves all coordinates from the longer 1-mask and the shorter 2-mask, matching the 4-by-3 output.
- In demo 3, only the shared normalized coordinates survive, matching the 2-by-3 output.

Implemented one direct set-based solver. No alternative revision was needed; the principal rejected shortcut is combining absolute coordinates, which cannot explain the widely separated objects producing a compact output.
