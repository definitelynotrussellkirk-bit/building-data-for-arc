# Solve work log

## Prior exposure

I had not opened task `89c85768abe1`'s generator, rule, notes, reference solutions,
private labels, or audit records before this solve. I used only the visible examples
printed by `python3 review.py blind prepare` and the starter files in `solve-blind/`.

## Revision 1 — bounding rectangles

**Observation.** Every nonzero color appears at two locations in each input. In the
output, all cells in the inclusive axis-aligned bounding rectangle of those two
locations are painted that color:

- example 0, color 4: `(3,7)` and `(4,10)` become a `2 × 4` rectangle;
- example 1, color 8: `(6,3)` and `(9,0)` become a `4 × 4` rectangle;
- example 2, color 6: `(6,6)` and `(7,10)` become a `2 × 5` rectangle.

The same explanation accounts exactly for every changed cell and color count in all
three demonstrations. The rectangles in the demonstrations are disjoint, so the
examples do not identify an overlap priority. I preserve deterministic input/color
scan order if an unseen input contains overlapping rectangles; this uncertainty is
not relevant to the shown instances.

**Implementation.** Copy the grid, collect all nonzero cells by color, and fill each
color's row/column bounding box inclusively. This also naturally handles a color with
more than two cells by filling its full bounding box, though the observed task uses
pairs.
