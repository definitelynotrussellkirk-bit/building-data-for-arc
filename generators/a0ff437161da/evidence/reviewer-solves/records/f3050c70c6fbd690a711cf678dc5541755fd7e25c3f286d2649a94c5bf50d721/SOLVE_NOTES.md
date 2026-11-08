# Solve work log

I had no earlier exposure to this task's generator, rule, private labels, or prior
solution explanations. I used only the visible examples printed by `blind prepare`.

## Revision 1 — concentric-ring counterclockwise segment

Each input has one non-background cell. The top-edge examples extend left to the
top-left corner, while the right-edge example extends up to the top-right corner.
Those are both the counterclockwise directions along the outer rectangular ring.
A rule that merely extends to an outer border would not explain useful behavior
for the two interior queries. I therefore generalized the grid to nested rectangular
rings: the cell's minimum distance to an outer edge is the ring inset; extend along
the side on which the cell lies to the preceding corner of that inset ring.

For side ties I use deterministic order top, right, bottom, left. This matters for
test query 0, whose marker is on the one-row central ring (equal top and bottom
distance); the program treats it as the top side and extends left to that ring's
left corner. Test query 1 is on the bottom side of inset ring 2 and extends right
to that ring's bottom-right corner. The visible examples do not independently
establish the center tie convention, so that remains the main uncertainty.
