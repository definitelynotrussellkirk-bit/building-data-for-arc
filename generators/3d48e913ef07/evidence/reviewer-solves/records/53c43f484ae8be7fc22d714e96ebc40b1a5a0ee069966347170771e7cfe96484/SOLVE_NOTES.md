# Solve work log

## Prior exposure

Before this visible-only episode I had already reviewed this task's generator and
canonical rule, so earlier rule exposure is **yes**. During this solve I did not
open the generator, Racket source, private labels, reference solutions, or prior
solution explanations. I used only `solve/challenge.json` and checker feedback.

## Revision 1 — ordered component packing

The three visible examples each contain:

1. three isolated nonzero/non-3 cells in the first column, which behave as a
   top-to-bottom color palette;
2. three 4-connected color-3 objects elsewhere;
3. an output made from cropped versions of those objects, recolored in palette
   order and stacked vertically with one all-zero row between crops.

The object order is descending **cell count**, not reading order: for example,
one visible input places a smaller component before a larger one spatially, but
the larger crop appears first. I implemented 4-connected component extraction,
descending-area ordering with a top-left tie-break, tight cropping, recoloring,
and left-aligned vertical stacking. No deliberate negative or diagnostic
revision was needed.
