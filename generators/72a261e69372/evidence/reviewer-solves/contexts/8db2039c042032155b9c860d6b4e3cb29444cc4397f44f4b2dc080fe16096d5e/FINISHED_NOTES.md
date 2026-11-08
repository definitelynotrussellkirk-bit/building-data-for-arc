# Solve notes

## Exposure

This is the required post-repair episode. I had already inspected the task rule and generator while repairing them, so this is **not blind**. During this episode I used only `solve/challenge.json` and did not reopen the generator, Racket source, reference solution, or private labels.

## Visible-example hypothesis

The colored nonzero objects are rectangular outlines. Color-1 cells are probes. In the nested examples, each probe becomes the color of the smallest rectangular outline whose interior strictly contains it: the inner probe takes the inner-frame color, a probe between nested outlines takes the next frame, and a probe outside inner frames takes the outer frame.

The overlap examples distinguish an intact frame from a mere bounding box. One color has been crossed/overwritten by another rectangle, leaving a broken outline. A color-1 probe inside that broken color's bounding box remains 1 when no intact outline encloses it. Therefore a valid frame must be one 4-connected same-color component equal to the complete perimeter of its own bounding box.

## Implementation plan

1. Find 4-connected components separately for every color except 0 and 1.
2. Retain a component only when it exactly equals a rectangular bounding-box perimeter with nonempty interior.
3. For each color-1 cell, collect intact frames that strictly contain it.
4. Replace it with the color of the minimum-area enclosing frame; leave it unchanged if the set is empty.

This directly handles both visible test scenes: nested frames and an occluded/broken frame crossed by a later intact one.
