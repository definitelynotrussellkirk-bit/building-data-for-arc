# Solve notes

## Revision 1 — odd straight blue components

From the three visible examples, only color-1 components change. A horizontal or
vertical straight color-1 component of odd length at least three has exactly its
middle cell recolored from 1 to 2. Even straight components, bent/branched color-1
components, and all nonblue components stay unchanged.

Checks against the visible examples:
- length 7 and length 3 straight blue components are marked at their centers;
- length 4 and length 2 straight blue components remain unchanged;
- a bent three-cell blue component remains unchanged;
- a nonblue length-5 line remains unchanged.

Implementation: find 4-connected blue components, test straightness and odd
length, then recolor the orientation-ordered midpoint in a copied grid.

Earlier exposure: yes. I had already inspected the task rule while repairing its
generator, so this is an exposed visible-only solve, not a blind inference claim.
During this solve I read only `solve/challenge.json`; I did not consult the
Racket source, generator implementation, reference outputs, private labels, or
previous solve explanation.
