# Solve work log

Earlier exposure: none. I did not inspect any generator, Racket rule, reference
solution, private label, or prior notes before this solve.

## Revision 1

Hypothesis: color-1 objects are separated by background and should be compared as
4-connected shapes. Every color-1 shape that occurs more than once in the same
input is recolored 3. Equality is translation-only: the horizontal and vertical
three-cell lines in train example 2 are rotations of one another but remain blue,
while the repeated 3x3 blocks become green. Non-blue objects are distractors and
remain unchanged.

Implementation: enumerate 4-connected color-1 components, normalize each by its
minimum row and column, count exact normalized coordinate signatures, and recolor
all components whose signature count exceeds one.

Remaining uncertainty: the visible examples do not distinguish 4-connectivity
from slot-based segmentation for disconnected multi-part motifs. Every shown
color-1 object is connected, so the simpler connected-component interpretation is
used.
