# Visible-only blind solve work log

This is an authored work log, not a captured token-level conversation.
No generator, reference rule, private labels, notes, or solutions were opened.

## Hypothesis before revision 1

All visible inputs use a zero background and one nonzero marker color.
The output is the perimeter of the markers' axis-aligned bounding rectangle,
in that marker color, on an otherwise zero grid of the same shape.
Example 1 is decisive: its additional point at (2, 4) is inside the rectangle
and disappears. Thus the operation replaces the point set with the outline;
it does not merely add an outline while preserving interior points.
Examples 0 and 2 locate opposite corners in different orientations, supporting
minimum/maximum coordinates rather than a fixed orientation or side length.

## Revision 1 and check

Implemented a fresh zero grid and colored precisely the bounding perimeter.
The program also makes the natural line/single-cell extension when bounding
dimensions collapse; such cases are not established by these demonstrations.
Ran the supported visible-example/execution checker. Query labels are withheld.
No deliberate negative or accidental failed revision has been manufactured.

## Stopping decision

Stop if all three visible demonstrations match and both queries execute.
Remaining uncertainty: behavior for multiple foreground colors or nonzero
backgrounds is not taught by this challenge. Hidden-query correctness is unknown.
