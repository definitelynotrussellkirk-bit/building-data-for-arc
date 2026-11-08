# Solve work log

I had not opened this task's generator, Racket rule, canonical row, prior solutions,
or private query labels. I had only read the packet-wide instructions and the visible
`solve-blind/challenge.json` prepared for this episode.

## Revision 1 — rotation token, ray stamping, and blockers

The four demonstrations can be decomposed into repeated copies of the color-1
polyomino. The lone non-reserved color selects a quarter-turn: 2 = identity,
3 = 90 degrees clockwise, 4 = 180 degrees, and 6 = 90 degrees counterclockwise.
The color-8 cell is the top-left anchor of the first rotated copy. The next anchor
is obtained by moving from 7 toward 8, i.e. adding `(row8-row7, col8-col7)`.
Copies continue until a filled motif cell would leave the grid or land on a gray
(color-5) blocker; the blocked copy is not drawn. All drawn cells become 9 and
all other input content is erased.

Evidence from the examples:

- Instruction 3 rotates the six-cell motif clockwise and stamps it at anchors
  `(5,11)`, `(3,11)`, `(1,11)`; the next anchor is out of bounds.
- Instruction 4 rotates its motif 180 degrees. Downward anchors `(8,3)` through
  `(11,3)` are legal, while the next copy would cover the gray cell `(13,4)`,
  explaining why propagation stops before the lower boundary.
- Instruction 6 rotates counterclockwise and moves up-left from `(5,4)` by
  `(-2,-1)`, producing exactly the three visible copies before clipping.
- Instruction 2 leaves the motif unchanged and moves upward from `(6,9)` by two
  rows, yielding four copies through the top boundary.

The main alternative considered was that the instruction color encoded a copy
count. That fails on the color-2 example, which contains four decomposable copies,
and the gray-adjacent stopping witness in the color-4 example supports the blocker
interpretation instead.
