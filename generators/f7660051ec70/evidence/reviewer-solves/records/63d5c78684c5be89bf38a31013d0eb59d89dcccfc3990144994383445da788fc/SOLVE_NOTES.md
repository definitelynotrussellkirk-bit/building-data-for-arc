# Solve work log

I had no earlier exposure to this task's generator, rule, reference solution, private labels, or earlier solve notes. I used only the visible examples produced by `python3 review.py blind prepare`.

## Revision 1 — marker selects a framed region

**Observation.** Every non-background object is a hollow rectangle bordered in blue (`1`). Only rectangles containing one or more red (`2`) cells change. In such a rectangle, every black (`0`) interior cell becomes green (`3`), while the blue border and red markers are preserved. Rectangles without red stay unchanged. This accounts for all three visible training examples, including examples with several rectangles and several red markers.

**Implementation.** Find each 4-connected blue component, accept it only when it is exactly the perimeter of its bounding rectangle, inspect that rectangle's interior for red, and fill its remaining black interior cells green when red is present.

**Alternatives considered.** A transformation based on rectangle size or on choosing a unique rectangle does not fit: training example 1 has two red cells in the same small frame, and only that frame changes; training example 2 selects a frame by marker presence rather than size. Filling a local neighborhood around each red cell also fails because the entire frame interior is filled, including cells far from the marker.

**Expected queries.** Query 0 fills the two non-red interior cells of its upper frame and leaves the lower unmarked frame untouched. Query 1 fills both marked frames independently and leaves the unmarked lower-left frame untouched.
