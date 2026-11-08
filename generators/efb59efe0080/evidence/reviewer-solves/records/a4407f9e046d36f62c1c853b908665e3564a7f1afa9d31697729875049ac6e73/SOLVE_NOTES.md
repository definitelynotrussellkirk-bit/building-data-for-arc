# Post-repair solve work log

This is a human-visible work log. I had already reviewed this task's generator, so this is **not blind**; I did not reopen the generator, Racket rule, private labels, reference solutions, or earlier solution explanations during this solve episode.

## Visible-example hypothesis

Each input has one red (2) object and one green (3) object at unrelated absolute positions. Absolute placement and the large background are discarded. For each color separately:

1. crop the object to its own bounding box;
2. align the two cropped masks at their top-left corners on a common canvas;
3. mark cyan (8) where exactly one mask is occupied (symmetric difference / XOR);
4. crop away any all-zero outer rows or columns from that XOR result.

The examples rule out physical-position overlay because their outputs are tiny, and they rule out union because cells occupied in both normalized masks become 0. The first and third examples also require the final content crop rather than returning the whole max-bbox canvas.

## Revision 1

Implemented the rule directly with normalized coordinate sets and set symmetric difference. The final crop is computed from the XOR cells themselves. No diagnostic or deliberate negative revision was used.
