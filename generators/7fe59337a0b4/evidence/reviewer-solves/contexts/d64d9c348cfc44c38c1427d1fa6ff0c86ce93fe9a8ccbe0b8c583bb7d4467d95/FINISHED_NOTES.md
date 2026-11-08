# Solve work log

## Exposure declaration before solving

I had only read the packet-wide start/duty documentation and the public visible
examples printed by `python3 review.py blind prepare`. I had not opened this
task's generator, Racket rule, notes, solutions, audit evidence, or private
query labels.

## Revision 1 — four rotated copies around the marker

Hypothesis from the eight visible training pairs:

- Color 9 is a fixed center marker.
- The other nonzero cells form one rectangularly cropped motif.
- The output erases the input occurrence and stamps four copies around color 9.
- The top copy keeps the motif's absolute orientation; right, bottom, and left
  are successive 90-degree clockwise rotations.
- Every copy has one wholly blank row or column between its bounding box and
  the marker. On the perpendicular axis, placement starts at
  `marker - floor(size / 2)`, which explains the visible examples with even
  motif sizes.

I implemented that rule directly, preserving the motif's colors and internal
zero cells and retaining the marker. The implementation returns the input
unchanged when the expected unique marker or motif is absent; clipping is only
a defensive behavior and is not needed by the displayed cases.

Alternative considered: rotate according to the input motif's original compass
position. Example 1 rejects this because its input motif is southeast of the
marker while the output's top copy still has the unrotated input orientation.

Remaining uncertainty before checking: whether hidden inputs can place a copy
against an edge. The public examples appear constructed with enough margin; the
implementation clips defensively rather than changing the output size.
