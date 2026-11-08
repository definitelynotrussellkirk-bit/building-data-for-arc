# Visible-only blind solve log

I opened only the prepared visible examples and queries for this solve. I have
not read this task's generator, rule, notes, reference solution or audit evidence,
and I have not opened the repair generator.

## Revision 1

Hypothesis: blue (1) outlines enclose rooms. A red (2) cell anywhere inside a
room activates that room, filling its entire interior yellow (4), including
its red markers. Blue outlines and unmarked rooms stay unchanged. Red cells
outside every closed room stay red.

Visible example 0 rules out replacing red markers alone: surrounding zero cells
also change to yellow. The unmarked top room rules out filling all rooms.
Example 1 shows that one or multiple red markers have the same activation effect
and that narrow interiors are allowed. Example 2 shows that nearby exterior red
markers do not activate an empty room; all three exterior reds are preserved.

Implementation: explore connected non-blue regions using four-neighbor flood
fill. Regions touching the canvas border represent the exterior. Fill a
non-border region only when it contains red. This uses the visible closed-room
structure without hard-coding the query dimensions, room count or positions.

I will check this single genuine hypothesis against the visible examples.
Masked query correctness remains unknown pending maintainer scoring.
