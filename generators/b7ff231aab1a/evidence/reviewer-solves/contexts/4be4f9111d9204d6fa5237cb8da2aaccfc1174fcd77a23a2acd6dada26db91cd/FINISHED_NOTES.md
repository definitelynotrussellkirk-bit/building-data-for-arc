# Solve work log

## Exposure declaration before solving

This is an **exposed post-repair solve**, not a blind solve. Before preparation I
had already read the selected generator and canonical rule while repairing the
task. During this solve phase I did not reopen the generator, Racket source,
canonical ledger, reference solutions, or private query labels. I used only the
visible presentation produced by `solve_episode.py prepare` and visible-check
feedback.

## Revision 1

The three visible demonstrations each contain exactly three 4-connected blue
(1) components with distinct areas and a horizontal group of one, two, or three
maroon (9) cells. The output shape and cyan-cell count match a tight crop of the
blue component whose increasing-area rank equals the maroon-cell count, expanded
2× in both dimensions and recolored cyan (8). Reading order is visibly not a
reliable selector: in each generated demonstration, spatial order and area order
are deliberately different.

Implementation:

1. Find all 4-connected color-1 components.
2. Count every color-9 cell to obtain one-indexed rank K.
3. Sort components by `(area, top row, left column)` and select rank K.
4. Crop the selected component's bounding box from the input.
5. Replace each source cell by a 2×2 block; map nonzero to 8 and zero to 0.

The top-left tie break is defensive only; visible component areas are distinct.
No alternative revision was needed unless visible checking exposed a mismatch.
