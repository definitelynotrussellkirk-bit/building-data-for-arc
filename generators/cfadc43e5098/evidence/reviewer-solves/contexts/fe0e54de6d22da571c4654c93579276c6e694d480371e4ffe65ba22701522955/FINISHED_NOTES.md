# Solve work log

I had not opened any generator, Racket rule, reference solution, task notes, or
private query labels before this blind solve.  I used only `challenge.json` and
local Python inspection.

## Revision 1 — inset bridges between aligned equal-colour rectangles

The training pairs contain separated solid rectangles.  The output preserves all
input cells and paints colour 8 only in zero-valued gaps.  A bridge appears when
two rectangles of the same colour are horizontally or vertically aligned.  Its
cross-section is the overlap of their projections with one cell removed from
each side: e.g. overlap width 3 gives a one-cell-wide vertical bridge, overlap
width 6 gives width 4.  Different-colour aligned rectangles are not joined.

I implemented connected-component rectangle detection, then considered each
same-colour pair.  For a horizontal pair I fill the column gap on the interior
of the shared row span; the vertical case is symmetric.  I require at least a
three-cell overlap and a zero-valued corridor in the original input, preventing
a bridge through an existing object.  Remaining uncertainty is whether a hidden
instance can contain three collinear same-colour rectangles; the zero-corridor
check should restrict connections to unobstructed pairs.
