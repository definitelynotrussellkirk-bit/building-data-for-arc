# Solve work log

Earlier exposure: none. I did not open any generator, rule, reference solution,
private label, audit record, or prior solve explanation before this attempt.

## Revision 1 — extreme colors fill each wall-bounded component

The color-5 cells form walls. Each four-connected non-5 component is a room.
Across the visible examples, a room with one nonzero color is filled solid with
that color. A room with multiple nonzero colors is filled as a checkerboard
using the numerically smallest and largest observed colors; any intermediate
color is a distractor. The smallest color occupies the parity class containing
the room's top-left bounding-box cell, and the largest occupies the other class.

Evidence from the examples:
- rooms containing `{4,7}`, `{1,2}`, or `{4,8}` alternate min/max;
- rooms containing `{1,4,9}` use only 1 and 9, and `{3,4,8}` use only 3 and 8;
- single-color rooms become solid;
- parity restarts independently in each room rather than using global grid parity.

Implementation: find four-connected components excluding wall color 5, collect
nonzero seed colors, and fill each component according to the rule above. I used
the component bounding box's minimum row/column as the local parity origin so
irregular rooms still follow the demonstrated local checkerboard.

Remaining uncertainty: a component with no nonzero seed is left unchanged, since
that case is not shown. More than three seed colors are treated by the same
minimum/maximum rule.
