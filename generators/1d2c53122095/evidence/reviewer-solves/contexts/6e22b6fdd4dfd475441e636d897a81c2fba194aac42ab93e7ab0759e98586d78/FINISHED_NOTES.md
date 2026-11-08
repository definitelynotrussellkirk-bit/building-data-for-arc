# Solve work log

This is an **exposed** post-repair solve. Before preparation I had already read and
worked on this task's generator and rule, so earlier rule exposure is `yes`. During
this solve episode I used only the visible presentation produced by `prepare` and
did not consult the generator, Racket source, reference solutions, or private labels.
These notes are my human work log, not a captured model trace.

## Revision 1

Visible-example hypothesis:

- The color-4 objects are strictly nested rectangular outlines.
- The number of red color-2 cells in row 0 is a one-based depth index.
- Sort the yellow frames from largest/outermost to smallest/innermost.
- Fill color 8 in the selected frame's interior, stopping at the next inner frame.
  When the selected frame is innermost, fill its center.

The four examples independently show depths 1, 2, 4, and 1. In particular, the
19x23 example with four red markers fills only the five-cell center of the fourth
frame, while the one-marker examples fill the outer ring despite different scene
sizes. That rules out selecting by canvas size or a fixed frame.

Implementation probe: detect color-4 connected components, take their bounding
boxes, sort by area, count top-row red cells, then recolor only zero cells inside
the selected box and outside the strict interior of the next box. The component
approach avoids assuming fixed coordinates, frame count, square shape, or gap.
