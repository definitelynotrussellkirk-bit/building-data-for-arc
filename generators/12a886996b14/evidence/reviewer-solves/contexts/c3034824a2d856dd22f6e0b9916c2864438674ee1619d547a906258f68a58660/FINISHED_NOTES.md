# Solve notes

## Visible hypothesis

The red (2) and green (3) objects represent the same marker at two locations.  The displacement from the top-left of the red bounding box to the top-left of the green bounding box is the motion vector.  The output is a fresh zero grid containing only the yellow (4) cells shifted by that vector.

Train example 0 gives red anchor `(4,0)` and green anchor `(6,4)`, hence `(dr,dc)=(2,4)`; shifting yellow from rows 3–5, columns 2–3 produces the displayed rows 5–7, columns 6–7.  Train example 1 is important because yellow appears to cover part of the red marker: the visible red anchor is `(5,10)`, green anchor `(3,6)`, and the same bbox-anchor rule gives `(-2,-4)`, matching the output.  Train example 2 similarly gives `(-2,+4)`.

I implemented that rule directly, preserving all yellow cells and dropping the red/green markers and original yellow placement.  The bounds guard is defensive; every visible example is arranged so the translated yellow object remains in the grid.
