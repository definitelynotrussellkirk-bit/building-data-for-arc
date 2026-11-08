# Solve work log

## Exposure declaration before solving

I had not opened task `69b886e1df03`'s generator, Racket rule, reference
solution, private labels, audit records, or any earlier solution explanation.
I used only `solve-blind/challenge.json` and my own analysis.

## Revision 1 — complete bent objects to rectangles

**Observation.** In every training pair, a colored 4-connected component that
spans more than one row and more than one column is completed to its solid
axis-aligned bounding rectangle. Straight horizontal or vertical components and
single cells are unchanged. Examples include the 3x2 color-9 component in train
1, both bent color-4 components in train 2, and the color-8 component in train 3.

**Hypothesis.** Find each nonzero 4-connected monochromatic component. If its
bounding box has both height and width greater than one, fill that entire box
with the component color; otherwise leave it alone.

**Predicted test changes.** Test 1 should add two 9s, one 5, and one 7 while
leaving the vertical 3 line unchanged. Test 2 should complete the upper 9's 3x2
box and the 5's 2x3 box, while leaving the horizontal 4 and lower horizontal 9
components unchanged.

**Alternatives considered.** A rule based on color identity is contradicted by
train 2, where some color-4 components change and no special color is privileged.
Filling the bounding box of every same-color set would wrongly merge the two
separate color-9 components in test 2. Using 4-connected components avoids that.
An 8-connected interpretation is not needed by any visible example and could
merge diagonally touching objects, so I kept the narrower 4-connected rule.

**Remaining uncertainty.** The visible examples do not distinguish “fill every
non-linear component” from a minimum-size condition, but all changed components
span both axes and the geometric rule is the simplest consistent hypothesis.
