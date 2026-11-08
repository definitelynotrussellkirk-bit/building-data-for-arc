# Post-repair visible-only solve: 9971f3a5882c

This is an authored work log, not a token-level model trace. Earlier exposure is
**yes**: I reviewed the generator and canonical rule while authoring the repair.
During this solve I read only the newly prepared public challenge and wrote a
standalone Python program. I did not reopen any generator, Racket rule, reference
solution, earlier solution explanation, or private query label.

## Revision 1

The visible pairs keep the canvas dimensions and all magenta markers. Green
full rows and columns define one small rectangular lattice. Its outside lines
move to positions one cell inside the nearest marker on each occupied side.
An unmarked side stays in place. Internal lines retain their row or column
coordinates and extend across the expanded lattice.

In example 0, the top marker moves the top edge to row 1, and the nearer of the
two right markers sets the right edge at column 8. Example 1 retains the internal
column at 7 while extending the bottom edge. Example 2 retains the internal
horizontal line at row 9 and distinguishes the nearer of two left markers.
These observations support the implemented boundary mapping and marker
preservation. Submit one genuine solution attempt to the visible-only checker.
Both query outputs remain masked and their correctness is unknown here.
