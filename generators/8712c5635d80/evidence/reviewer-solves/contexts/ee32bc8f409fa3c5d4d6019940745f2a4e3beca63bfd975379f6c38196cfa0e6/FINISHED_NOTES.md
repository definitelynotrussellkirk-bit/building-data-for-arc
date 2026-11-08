# Solve work log

I had not opened the generator, Racket rule, private labels, reference solutions,
or prior audit material for this task before solving it.

## Revision 1

The grid consists of two equal square panels separated by a full-height color-9
column.  The left panel contains a small nonzero silhouette.  The right panel is
a hollow square frame.  In every demonstration, the output keeps the input and
paints the left silhouette into the *same row and panel-relative column* in the
right panel, using the right frame's color.  This is coordinate-preserving copy,
not bounding-box normalization: example 0's low/right-shifted source remains
low/right-shifted inside the destination frame.

Implementation: locate the all-9 divider, infer the destination paint from the
right panel's nonzero color, then shift each nonzero left-panel cell by
`divider + 1` columns and recolor it.  Remaining uncertainty is limited to inputs
with multiple left colors or a foreground on a destination border; the visible
examples do not require special handling for either case.
