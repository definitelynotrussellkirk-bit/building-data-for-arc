# Visible-only blind solve work log

Task: 038f266f3acf. This is an authored work summary, not a captured token trace.
Earlier rule exposure: no. Only the preparation tool's visible examples and
challenge were read; generator, canonical rule, notes and private answers stayed closed.

## Revision 1

Hypothesis: each nonzero rectangle has one red boundary marker. Extend outward
from that side to the canvas edge. The red marker becomes the center ray of a
green strip. Its radius is the rectangle depth in that direction minus one.
Existing rectangles remain in place and the canvas clips the new strip.

The four demonstrations show upward, downward and rightward extensions, depths
2 through 5, off-center markers, and clipping. The implementation uses connected
components and their bounds; it does not memorize example positions or sizes.
Leftward behavior is the symmetric extrapolation; it is not demonstrated here.
Corner markers and interacting extensions are not resolved by these examples.

Validation: run the visible-only checker. Masked query correctness remains
withheld; a visible pass is not a claimed private-query success.
