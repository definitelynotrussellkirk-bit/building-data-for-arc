# Solve work log

Earlier exposure: I had not seen task `d5a059b0f3a6`, its generator, its rule, its
solutions, or its private labels. I inspected only `challenge.json` and the
provided solve templates.

## Revision 1 — framed mirror completion

**Observation.** Every lesson contains three rectangles represented only by four
three-cell L corners of a non-1 color. The scattered 1s outside those rectangles
vanish. Inside each rectangle, one compact 1 motif is retained and copied by a
reflection. Lessons 1–2 reflect top-to-bottom; lesson 3 reflects left-to-right.
The same reflection direction is used for all three rectangles in a lesson.

**Probe.** I enumerated input/output difference coordinates and expressed each
in-frame 1 coordinate relative to the rectangle center. On the intended axis,
all motif cells occupy only one side (allowing center-line cells), and the
reflected copy adds new cells. On the other axis, at least one rectangle's motif
crosses the axis or already contains mirrored pairs. This exactly accounts for
all visible changes in all three lessons.

**Implementation.** Detect 4-connected three-cell L corners, pair TL/TR/BL/BR
corners into disjoint frames, choose the global reflection axis by the above
one-sidedness criterion, erase all 1 noise, then restore and reflect only the
1s inside frames. The marker color itself is not hard-coded.

**Remaining uncertainty.** A deliberately ambiguous lesson whose motifs are
one-sided with respect to both axes would need another cue. The visible lessons
include an unambiguous frame and consistently support the global-axis rule.
