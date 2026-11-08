# Solve notes

## Visible-only hypothesis

Each input has three separated single-colour objects.  Tight-crop each object and
test whether its occupancy mask is invariant under a left/right reflection.
When more than one object is symmetric, choose the earliest by top row and then
left column; output that object's original-colour bounding-box crop.

The examples distinguish this from "largest symmetric": train 1 selects the
smaller colour-2 T before the later colour-1 symmetric shape.  They also
distinguish it from "first object": train 0's first object is asymmetric.

Predictions before checking:

- Query 0: colour 2, `222 / 020`; the later colour-5 object is also symmetric.
- Query 1: colour 2, `222 / 202 / 222`; the colour-1 object is asymmetric and
  the later colour-4 T is symmetric.
