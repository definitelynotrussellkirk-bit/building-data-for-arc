# Solve work log

I had not opened the blind task's generator, Racket rule, canonical answer, prior
notes, or private labels before this solve. I had only read the packet-level
instructions and the visible `challenge.json`.

## Revision 1

**Observation.** Color 5 forms walls that partition each grid into 4-connected
rooms. In the first training pair, the middle-top room containing only color 2
is filled with 2, and the right room containing only color 3 is filled with 3.
The left room contains both colors 1 and 3 and is not filled. The empty
middle-bottom room is also unchanged. The second pair repeats this contrast:
single-color rooms are filled, an empty room is unchanged, and the room with
both 1 and 3 is unchanged. The third pair shows that several markers of the
same color still count as a single-color room and cause a fill.

**Hypothesis.** Treat every maximal 4-connected component of cells not equal to
5 as a room. Collect its distinct nonzero colors. If there is exactly one such
color, replace every cell in that room by the color. If there are zero or two or
more distinct marker colors, leave the room unchanged. Preserve all 5 walls.

**Implementation.** Flood-fill each non-wall component, collect its cells and
nonzero colors, then fill only components with a singleton color set. This also
handles rooms touching the edge and arbitrary wall layouts rather than assuming
rectangles.

**Expected tests.** In test 1, all four rooms have one marker color and should be
filled (three with 1, one with 3). In test 2, the top room is mixed and remains
unchanged, the middle room is empty and remains unchanged, and the bottom room
fills with 1.

**Alternatives considered.** A rectangle-by-rectangle interpretation fits the
examples, but connected components are the more direct invariant and cover the
partial horizontal wall in training pair 1. Filling based on marker count would
fail the third pair, whose lower-right room has several color-1 markers but is
filled.

**Remaining uncertainty.** The examples consistently use 5 as the wall color
and 0 as background. I assume any other nonzero color is a marker and that
4-connectivity, rather than diagonal connectivity, defines rooms.
