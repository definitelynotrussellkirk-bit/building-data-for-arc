# Solve work log

## Isolation / prior exposure

I prepared this blind episode before opening the assigned generator, either task's
Racket rule, task notes, reference solutions, private labels, or earlier solution
explanations. I had not previously seen the rule for task `0a9926d504f3` in this
packet. Earlier rule exposure: no. Reference consulted: no.

## Revision 1 — extremal frame plus marker cross

**Hypothesis.** Ignore the zero background and use the non-red points to define a
rectangular frame. The topmost non-red point supplies the top edge's color, the
bottommost supplies the bottom edge, the leftmost supplies the left edge, and the
rightmost supplies the right edge. One point may define two sides. Horizontal
edges win at corners. Color 2 is a marker: draw color 5 horizontally and vertically
through it, but only inside the frame; retain the 2 only when it is strictly
interior. Rebuild the output from background, thereby removing interior distractors.

**Evidence from visible pairs.** In every example the four frame coordinates equal
the extrema of the non-2 points. Example 3 contains an extra interior color-1 cell
that disappears, which distinguishes extremal anchors from preserving all input
points. Example 2 places the 2 on the bottom edge; the bottom-edge color overwrites
it and only the interior part of the vertical gray arm remains.

**Probe / implementation.** Implemented the rule directly in `solution.py`, using
the modal input color as background and coordinate extrema among all nonbackground,
non-2 cells. The two test inputs exercise (1) one anchor defining both top and left
sides and (2) a marker lying on the top boundary.

**Alternatives considered.** A literal bounding box of all colored cells would put
the red marker into the extrema and does not explain boundary overwriting. Preserving
all seed cells contradicts the disappearing interior distractor. Drawing the cross
through the border contradicts example 2.

**Remaining uncertainty.** The examples do not define tie-breaking if two distinct
anchor colors share the same extremal row or column, or behavior with multiple 2s.
The generated visible instances appear to avoid those cases.
