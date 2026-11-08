# Solve work log

I had no earlier exposure to task `a2e752ad6948`, its rule, generator, private
labels, or previous solutions. I used only the visible examples produced by the
blind preparation step.

## Revision 1 — rectangular-frame checkerboards

The inputs contain two hollow, axis-aligned colored rectangles.  Each rectangle
has exactly one differently colored interior cell.  Comparing all three training
examples showed that the cell's *position is not the phase anchor*: in several
examples its original position becomes the frame color.  Instead, its color is
the second checkerboard color, and the checkerboard always starts with that color
at the top-left interior cell.  The original frame remains unchanged.

Implementation plan:

1. Group nonzero cells by color.
2. Recognize a frame color only when every perimeter cell of its color bounding
   box is present and the box has a nonempty interior.
3. Find the unique nonzero, non-frame interior color.
4. Fill the interior by parity from its top-left, alternating marker color and
   frame color.

This also avoids confusing the singleton marker colors with frame colors.  The
main remaining assumption is that each frame has exactly one distinct interior
marker color, which is supported by every visible example and query.
