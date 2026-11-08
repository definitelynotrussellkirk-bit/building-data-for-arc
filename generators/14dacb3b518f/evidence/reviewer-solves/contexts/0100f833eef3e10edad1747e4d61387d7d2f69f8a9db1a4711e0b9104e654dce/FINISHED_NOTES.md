# Solve work log

## Exposure declaration before solving

I had not seen task `14dacb3b518f`, its generator, its Racket rule, private labels,
reference solution, or prior solution notes. Before this solve I read only the
packet-level workflow documentation and then `solve-blind/challenge.json`.

## Revision 1 — enclosed-background classification

Across all four visible lessons, every connected cyan object is recolored as a
whole. Objects with one or more background cells fully enclosed by the object
become azure (8); objects without an enclosed background region become red (2).
This accounts for filled rectangles and open/incomplete frames becoming red,
while hollow frames and patterns with one or more sealed interior gaps become
azure.

I implemented 4-connected component extraction for all nonzero cells. For each
component, I construct its bounding-box mask, flood-fill background from the box
boundary, and classify any unvisited background cell as an enclosed hole. This
is preferable to merely counting zeros in a bounding box because open frames
also contain zeros but do not enclose them.

Remaining uncertainty: the visible examples use only color 6 for input objects
and spatially separated 4-connected objects. The program treats every nonzero
cell as foreground, which preserves the demonstrated object semantics without
hard-coding cyan.
