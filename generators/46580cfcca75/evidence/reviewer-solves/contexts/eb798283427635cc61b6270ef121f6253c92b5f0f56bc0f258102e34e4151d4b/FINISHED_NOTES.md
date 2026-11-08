# Solve notes

## Revision 1

Visible examples show one or two solid monochrome rectangles on a zero background.
Each output preserves the rectangle's bounding box and color but clears strictly
interior cells. Rectangles with a side of length 2 are unchanged because every
cell is already on the perimeter. The examples also show that objects are handled
independently rather than using one global bounding box.

Implementation hypothesis: find each nonzero same-color 4-connected component,
compute its tight bounding box, and draw only that box's perimeter on a fresh zero
grid. This also handles both test queries: a 3x3 block loses its center, while the
2x2 block in query 1 remains unchanged and the 5x3 block becomes a frame.

No Racket source, generator source, private label, or reference solution was
consulted during this solve phase. I had earlier rule exposure from the required
generator review, which will be declared honestly at finish.
