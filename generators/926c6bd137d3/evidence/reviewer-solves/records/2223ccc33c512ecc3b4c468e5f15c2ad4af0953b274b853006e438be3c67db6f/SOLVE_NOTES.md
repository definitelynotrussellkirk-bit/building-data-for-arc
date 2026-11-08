# Solve work log

## Exposure disclosure

I had inspected the repair target before this formal solve episode, so this is
not a blind rule-discovery claim.  During this episode I kept the generator,
Racket rule, reference solutions, private labels, and prior solve notes closed.
I used only the four examples and two unlabeled queries printed in `README.md`.

## Visible-example hypothesis

Every active object is a closed rectangular frame of yellow (`4`) cells.  Its
strict interior contains exactly one non-background, non-yellow marker.  The
output replaces every background (`0`) cell in that frame's interior with the
marker colour.  It leaves the yellow border, the marker, background, and all
coloured cells outside every frame unchanged.

Evidence from the visible pairs:

- Example 0 fills the sole yellow frame with its interior `7`, while two
  exterior `8` cells stay fixed.
- Example 1 independently fills the upper frame with `7` and the lower frame
  with `8`; all exterior `9` distractors stay fixed.
- Examples 2 and 3 repeat the same rule for differently sized frames, multiple
  marker colours, and exterior distractors of colours `1` and `9`.
- The fill covers the entire strict interior, not merely the marker row,
  marker column, or cells adjacent to the marker.

## Implementation

`solution.py` finds four-connected yellow components, takes each component's
bounding box, verifies that the entire rectangular border is yellow, reads the
non-zero/non-yellow marker in the strict interior, and fills only zero interior
cells with that colour.  The input is copied before editing, so exterior cells
and borders are preserved.

The rectangular-border check is a conservative guard against treating an
unrelated yellow fragment as a frame.  Remaining uncertainty is limited to
unseen malformed inputs (for example, multiple marker colours in one frame),
which are not supported by any visible example; the implementation uses the
first marker in that case rather than altering exterior data.
