# Solve work log

## Prior exposure

Before this blind solve I had not opened the task's generator, Racket rule,
reference solution, private query labels, or earlier solution notes. I used only
the visible examples printed by `solve_episode.py blind prepare` and the public
files in `solve-blind/`.

## Revision 1 — rectangle perimeter from the two color-3 markers

**Observation.** Every training pair contains exactly two color-3 cells. The
output preserves the full input and draws color 8 on the axis-aligned rectangle
perimeter for which those two cells are opposite corners. It only changes zero
cells: in training example 0 a color-1 cell already on the perimeter is retained.
Other isolated colored cells outside the rectangle are also retained and do not
select the rectangle.

**Implementation.** Copy the grid, locate the two 3s, compute their min/max row
and column, enumerate all perimeter coordinates, and replace only perimeter
zeros with 8. If the expected pair of 3s is absent, return the unchanged copy
rather than guessing.

**Alternatives considered.** A filled rectangle contradicts every example's
zero interior. Connecting the markers with only an L-shape or a shortest path
contradicts the complete four-sided outlines. Using all nonzero cells as a
bounding box contradicts examples containing an unrelated color outside the
rectangle.

**Remaining uncertainty.** The visible examples do not exercise a one-row or
one-column degenerate rectangle, but the implementation naturally draws the
available segment once and preserves both marker cells.
