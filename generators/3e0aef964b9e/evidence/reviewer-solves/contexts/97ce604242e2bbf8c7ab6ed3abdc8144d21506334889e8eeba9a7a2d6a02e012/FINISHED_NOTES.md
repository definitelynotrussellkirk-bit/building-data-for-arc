# Solve work log

## Prior exposure

Before this fresh solve I had already inspected the assigned generator and canonical rule while repairing it, so this is explicitly an exposed solve. During this solve phase I used only the displayed challenge and my own Python; I did not reopen the generator, Racket source, reference solutions, or private query labels.

## Revision 1 — count-matched convex-hull completion

The three visible pairs share these observations:

- The modal color is unchanged background.
- Exactly two non-background colors occur.
- Every cell of the sparse donor color disappears.
- The same number of background cells is recolored inside one object of the other color.
- The selected object is not consistently the largest, rectangular, lower-valued, or upper-valued color. In the sparse second example, the recolored cell completes the convex hull of a three-cell diagonal object; in the third, three donor cells fill three holes in an irregular object.

Hypothesis: split each non-background color into 8-connected objects, compute each object's filled convex hull, and select the unique object whose background-cell deficit equals the total cell count of the opposite color. Erase the opposite-color donor cells and paint that deficit with the donor color.

Implementation uses a monotone-chain hull over each occupied pixel's four corners and ray casting at cell centers. This handles diagonal/irregular objects rather than assuming rectangles. The remaining uncertainty is only the exact boundary convention, which the visible examples exercise sufficiently to compare through the official visible-only checker.
