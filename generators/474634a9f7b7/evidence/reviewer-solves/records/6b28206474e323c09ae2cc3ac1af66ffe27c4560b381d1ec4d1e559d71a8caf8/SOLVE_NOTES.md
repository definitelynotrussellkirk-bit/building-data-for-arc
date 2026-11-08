# Solve work log

I had not opened this task's generator, canonical rule, notes, solutions, audit
records, or the assigned repair generator before solving.  I used only the
visible grids in `challenge.json` and small scripts that compared visible train
inputs with visible train outputs.

## Revision 1 — quadrant-normalized transfer rule

Each example has four differently colored objects around the four quadrants.
The total number of non-background cells is conserved: the uniquely largest
object gains three cells, while each of the other three objects loses one.

Rotating each quadrant into a shared local frame makes the changes identical:

- `+x` points inward toward the grid centre;
- `+y` follows the clockwise/tangential direction shown by the shapes;
- every smaller object loses the occupied cell at local `(max_x, max_y)`;
- the largest object gains three cells at local `x=min_x-1` and
  `y=max_y-1, max_y, max_y+1`.

I checked the coordinate rule against all four visible pairs.  It reproduces
all twelve removals and all four three-cell additions exactly.  The program
identifies the background as the most frequent color, groups the remaining
cells by color, determines each object's quadrant from its centroid, applies
the local transforms, and maps the edits back to global coordinates.

Remaining uncertainty: the visible data always has four distinct object colors,
a unique largest object, and the distinguished smaller-object corner occupied.
The implementation follows that demonstrated domain and includes only a modest
deterministic fallback for an unexpected missing corner.
