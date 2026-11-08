# Solve work log

## Prior exposure

I had already reviewed this task's generator before this required post-repair solve, so earlier rule exposure is **yes**. During this solve I kept the generator, Racket rule, reference solutions, private labels, and earlier solution explanations closed and used only the visible examples in `solve/README.md` plus visible-only check feedback.

## Revision 1 hypothesis

The examples show that every 4-connected cyan (`8`) object is handled independently. Its bounding box supplies local coordinates. Only cyan cells are recolored, so an interior hole or edge notch remains background rather than being filled.

Within each object's bounding box:

- a centered inset region becomes yellow (`4`);
- the remaining cyan ring is divided by the bbox horizontal and vertical midlines into top-left magenta (`6`), top-right blue (`1`), bottom-left red (`2`), and bottom-right green (`3`);
- the inset thickness is `max(2, floor(min(height, width) / 4))`.

Visible probes supporting the formula: 6- through 10-cell minimum sides use a two-cell outer band, while the larger component uses a three-cell band. Odd dimensions are resolved by comparing `2 * local_coordinate` with the full dimension, matching the visible asymmetric halves. I implemented a 4-neighbor flood fill, one bbox per component, and recolored only cells belonging to that component. The main rival considered was painting whole bounding boxes; the visible holes/notches reject it because their zero cells stay zero.

Remaining uncertainty before checking: whether the inset rule could instead be a finite lookup table for the displayed sizes. The proportional formula is the simplest rule that covers all visible sizes and generalizes to the queries.
