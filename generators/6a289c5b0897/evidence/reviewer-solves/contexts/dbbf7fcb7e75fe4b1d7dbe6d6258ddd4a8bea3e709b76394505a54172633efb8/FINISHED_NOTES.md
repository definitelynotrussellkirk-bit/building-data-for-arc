# Visible-only solve notes

## Revision 1

I inspected only `solve/challenge.json` during this solve. Each input has gray `5`
obstacles, zero background, and exactly two cells of one other color. The output
erases everything except a connected orthogonal route, painted in the marker
color, between those two cells.

The route length in each visible example is shortest among paths avoiding gray.
Several shortest routes can exist, so “any shortest path” is insufficient. Using
the row-major first marker as the start and expanding a breadth-first search in
Up, Down, Left, Right order reproduces all three visible outputs. I implemented
that deterministic BFS, reconstructing the predecessor chain and returning an
otherwise-zero grid.

I had earlier exposure to the task rule while repairing the generator, so this is
not a blind solve. I did not reopen or consult the generator, Racket authority,
reference solution, or private query labels during this episode.
