# Solve notes

## Exposure

This is not blind: I had already reviewed this task's generator and canonical rule before `solve prepare`. During this solve I used only the prepared visible examples and did not reopen the generator, rule source, private labels, or earlier solution explanations.

## Visible-example hypothesis

Treat each nonzero color as one or more 4-connected components. A component changes only when its occupied cells are exactly the perimeter of its own axis-aligned bounding box and that box has an interior. In that case fill the entire box with the component color. Leave incomplete frames, solid rectangles, and other components unchanged.

Evidence from the visible pairs:

- Train 0 fills the closed color-4 frame while the color-2 frame missing a side stays unchanged.
- Train 1 fills the closed color-3 frame while the color-4 incomplete frame stays unchanged.
- Train 2 fills the closed color-8 and color-4 frames; the incomplete color-7 and color-3 components stay unchanged.

## Query predictions

- Query 0: fill the closed 8, 9, and 5 frames; leave the broken 2 frame and already-solid 7 block unchanged.
- Query 1: fill the closed 2 frame; leave the broken 8 frame unchanged.

## Implementation probe

Implement 4-connected same-color extraction, compute each component's bounding box, compare its cell set with the exact box border, then fill only exact borders. Preserve dimensions and all unaffected cells.
