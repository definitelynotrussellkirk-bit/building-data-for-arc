# Solve work log

## Exposure record

Before solving I had read only the packet-wide instructions and the assignment text.
I did not open this task's generator, Racket rule, reference solution, private query
labels, prior notes, or audit records.

## Revision 1 — exact oriented stencil copies

The input is split by a full-height column of 9s.  The left side contains one
3×3 red stencil: a vertical segment down the left edge joined to a horizontal
segment across the bottom.  The output has the dimensions of the region to the
right of the separator and places an 8 at the center of every exact copy of that
stencil in the same orientation.  Rotated copies are distractors.  Non-red noise
outside a candidate window does not matter, while noise inside the 3×3 window
prevents an exact match.

I checked the coordinates manually on all visible examples.  For example 0, the
same-orientation copies have centers (1,2) and (6,7), exactly matching the two
output markers; the connected rotated red corner near the first copy is not
marked.  The same rule accounts for both markers in examples 1 and 2.

Implementation plan: find the uniform nonzero separator column, crop the nonzero
bounding box from its left side as the stencil, scan exact windows on the right,
and mark each matching window's center with 8.  A local visible-example test was
run first against the unimplemented stub and failed with `NotImplementedError`.
No alternative rule was needed after the exact-copy hypothesis fit all examples.
