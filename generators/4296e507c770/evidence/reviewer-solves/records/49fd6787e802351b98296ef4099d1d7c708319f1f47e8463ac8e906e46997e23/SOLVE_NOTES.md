# Visible-only blind solve: 4296e507c770

## Exposure and allowed evidence

I had not opened this task's generator, Racket rule, notes, prior solutions,
audit records, or private labels, nor the assigned repair generator. The only
puzzle evidence used was the presentation from `solve_episode.py blind prepare`.
I have no known earlier exposure to this exact task.

## Hypothesis before the first implementation

All examples preserve the input dimensions: 12 × 18, 13 × 18, and 16 × 16.
The red (2) object supplies a template. Each isolated 3/4/5/6 cell specifies
the top-left of a transformed template's bounding box. Paint every copied
occupied cell azure (8) onto a blank canvas; omit the source and the markers.

- 3: unchanged template.
- 4: left-right reflection.
- 5: top-bottom reflection.
- 6: 90-degree clockwise rotation.

The first two examples contain a 3 × 2 template with rows `11 / 11 / 10`.
In example 1, marker 3 at (4, 10) gives that same shape. Marker 4 at (5, 3)
has its lone bottom cell on the right; marker 5 at (7, 2) has its lone top
cell on the left. Marker 6 at (5, 6) gives rows `111 / 011`, distinguishing
clockwise from counterclockwise rotation.

Example 2 has a 4 × 3 template with rows `001 / 111 / 010 / 010`. The
clockwise image is `0010 / 1110 / 0011`, matching the output next to the
marker at (6, 12). Its two marker-4 instances support repeated stamping.
These observations also show that the marker is a bounding-box anchor:
the transformed shape need not occupy the marker cell itself.

## Implementation and uncertainty

Revision 1 extracts all red cells, normalizes their bounding box, computes
the four transformations, and stamps at every matching marker. Coincident
copies form a union. Out-of-bounds cells are clipped; the visible examples
do not demonstrate clipping, so this is a defensive implementation choice,
not a rule independently established from those examples. No alternative
solver revision or deliberate failure was manufactured.

## Visible checker result and stopping reason

Pending the first check. Query answers and even their output dimensions are
withheld; any agreement claim will concern the visible examples only.
