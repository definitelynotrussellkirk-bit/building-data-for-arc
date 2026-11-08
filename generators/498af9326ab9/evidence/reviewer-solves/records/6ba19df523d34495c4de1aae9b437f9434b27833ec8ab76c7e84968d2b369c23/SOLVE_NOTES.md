# Solve work log

## Prior exposure

Before this blind solve I had not opened the task's generator, Racket rule, canonical
record, reference solutions, audit evidence, or earlier solution explanations. I used
only the visible examples printed by `python3 review.py blind prepare` and the files in
`WORK/solve-blind/`.

## Revision 1 — union of shortest paths

The blue cell (1) and red cell (2) behave as endpoints, gray cells (5) as blocked
cells, and azure (8) marks every passable cell that belongs to at least one shortest
four-neighbor path between the endpoints.

Evidence from the visible examples:

- In example 0, the gray rectangle makes the one-row detour above it uniquely
  shortest. The output is exactly the union of all such top detours.
- In example 1, equally short detours exist above and below the gray rectangle.
  Their union, including all shortest approach choices on either side, fills the
  displayed five-row band.
- In example 2, the nearest openings in the gray wall are equally distant above
  and below the endpoint row. The union of shortest paths through either opening
  fills the band between those openings while preserving gray cells.
- With no gray obstacle, the rule predicts the full axis-aligned rectangle between
  diagonally separated endpoints, because every monotone cell in that rectangle is
  on some Manhattan-shortest path.

Implementation: run BFS from each endpoint while treating color 5 as impassable.
A passable cell is colored 8 exactly when `dist_from_1 + dist_from_2` equals the
shortest endpoint distance. Colors 1, 2, and 5 are preserved. If the endpoints are
unreachable, the input is returned unchanged rather than inventing a path.

Remaining uncertainty: the examples use fixed semantic colors 1, 2, 5, and 8; I
implemented those exact roles rather than inferring them from frequency.
