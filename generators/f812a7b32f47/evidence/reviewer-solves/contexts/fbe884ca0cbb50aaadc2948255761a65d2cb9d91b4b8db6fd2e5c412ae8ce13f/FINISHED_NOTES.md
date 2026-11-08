# Solve work log

## Exposure declaration before solving

I had already inspected and repaired this task's generator and canonical rule before this exposed solve, so this is **not blind**. During this solve episode I did not reopen the generator, Racket source, reference solution, private labels, or earlier solution explanations; I used only `solve/challenge.json` and my own Python.

## Revision 1 — bbox-edge row/column intersections

Across all three visible examples, the nonzero cells form a hollow rectangular frame. Color 2 on the frame's left edge marks rows, and color 3 on the frame's top edge marks columns. The output writes 7 at every interior crossing of those marked rows and columns, preserving the frame and all other cells.

The examples also contain misleading marker-colored cells on other edges: color 2 on the bottom and color 3 on the right. Those do not participate. This distinguishes an edge-role rule from an anywhere-in-row/column shortcut. I implemented the rule from the nonzero bounding box and intentionally scan only the left-edge interior for 2 and top-edge interior for 3.
