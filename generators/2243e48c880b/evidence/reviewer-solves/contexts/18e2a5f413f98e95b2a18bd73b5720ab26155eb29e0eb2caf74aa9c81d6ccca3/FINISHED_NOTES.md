# Solve notes

Human work log based only on the three visible demonstrations prepared for this
episode. I did not inspect the generator, Racket source, private labels, or prior
solution files during this phase.

Hypothesis: treat each nonzero monochromatic 4-connected region as an object,
ignore its original color, rank the three objects by cell count, and recolor the
smallest/middle/largest objects 2/4/8 on a blank grid.

The first example contains sizes 6, 5, and 5. The two size-5 objects become 2
and 4 in their top-left discovery order, while size 6 becomes 8. The second
example independently confirms the same tie rule: two size-6 objects become 4
then 8 in row-major component order, while size 3 becomes 2. The third example
has distinct sizes 2, 3, and 5 and confirms the ascending mapping directly.

Implementation: scan cells row-major, flood-fill same-color orthogonal
components, use Python's stable size sort, and paint ranks 2, 4, 8. This also
handles disconnected regions of the same input color as separate objects.
