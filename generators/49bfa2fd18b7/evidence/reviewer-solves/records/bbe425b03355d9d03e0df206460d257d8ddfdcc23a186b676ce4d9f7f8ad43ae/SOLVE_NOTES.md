# Solve work log

I had not opened the blind task's generator, Racket rule, reference solutions,
private labels, prior notes, or the assigned repair generator before this solve.
I used only `solve-blind/challenge.json` and local scripts that parsed those visible grids.

## Revision 1

The inputs contain several 4-connected color-6 objects plus exactly two color-5
cells. Every visible output is a cropped color-6 object recolored to 2. I first
considered whether the color-5 domino pointed spatially to the chosen object, but
training example 2 contradicts a nearest-object rule: its selected object is the
far lower-right component rather than the component closest to the marker.

I enumerated all 4-connected color-6 components from the visible examples and
compared their areas with the output. Their descending areas are:

- train 1: 7, **5**, 3, 2; output is the area-5 object
- train 2: 7, **4**, 3; output is the area-4 object
- train 3: 5, **4**, 3; output is the area-4 object

Thus the two color-5 cells appear to encode rank 2: choose the second-largest
color-6 component, crop to its bounding box, preserve its shape, and recolor its
cells from 6 to 2 while keeping bounding-box background cells 0. The test inputs
have descending component areas 5, 4, 3 and 9, 6, 5, 4, so the predicted outputs
are respectively the area-4 and area-6 objects. Remaining uncertainty is how ties
would be resolved, but no visible example or query has a tie at rank 2.
