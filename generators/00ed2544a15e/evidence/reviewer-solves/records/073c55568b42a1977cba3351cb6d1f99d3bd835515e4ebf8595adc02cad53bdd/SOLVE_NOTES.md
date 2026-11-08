# Solve work log

I had not opened the blind task's generator, Racket rule, canonical record, prior
solutions, or private labels. I used only the visible examples emitted by
`solve_episode.py blind prepare`.

## Revision 1 — unobstructed three-ray red hub

The six red (`2`) cells contain one hub with three orthogonally aligned red
endpoints. Output color `8` fills only the zero-valued interior cells between the
hub and those endpoints. The two-cell non-red object is preserved and can block
a nominal fourth red alignment: in train example 2, the red at `(3,11)` is not
connected to hub `(3,8)` because color `3` at `(3,10)` interrupts the segment.
The remaining red cells are distractors.

I implemented this by examining each red cell, taking the nearest red cell in
each cardinal direction, rejecting any segment whose interior contains a
nonzero cell, and choosing the red cell with the largest number of clear rays.
The visible examples imply the intended hub has three clear rays. I then color
their zero interiors azure (`8`) while preserving all endpoints and obstacles.

Predicted query structure:

- Query 0 hub `(4,4)`: connect left to `(4,1)`, right to `(4,7)`, and down to
  `(7,4)`; the vertical red alignment in column 7 is blocked by the `7` object.
- Query 1 hub `(5,3)`: connect up to `(2,3)`, right to `(5,7)`, and down to
  `(8,3)`.

Remaining uncertainty: the examples do not show two candidate hubs tied at three
clear rays. The implementation deterministically takes the first maximum, but
all visible tasks have a unique maximum.
