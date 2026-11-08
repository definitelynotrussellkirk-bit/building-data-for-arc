# Blind solve notes — d2534264df36

## Visible-only observations

- Every nonzero input cell lies at an odd row and odd column; even rows and
  columns are zero spacers.
- The output keeps the same dimensions and only writes on that compressed
  odd-coordinate lattice.
- A direct four-way reflection of the sparse cells is insufficient: in train 0,
  the two color-2 cells expand into complete outer edges, not just reflected
  points.
- On the compressed lattice, each sparse cluster describes one inset rectangular
  frame.  A colored frame corner gives all four corner cells.  Colored samples
  along the horizontal and vertical sides give the colors used to complete the
  corresponding full sides.  Zero samples mean that side remains zero.
- The fragment can be shown at any corner: train 1 uses upper-left fragments,
  train 0 lower-right, and train 2 lower-left.  Classifying cells by inset shell
  rather than absolute corner handles all orientations.

## Implementation hypothesis

Compress to odd row/column coordinates.  For each concentric shell, collect the
nonzero corner color, horizontal-side color, and vertical-side color visible
anywhere on that shell, then paint the full symmetric shell.  Expand back into a
zero-filled grid with the original dimensions.

The two queries appear to use upper-right fragments.  Query 0 encodes corner-only
shells 0 and 2, a color-2 shell around color-1 corners at inset 1, and a color-7
shell around color-8 corners at inset 3.  Query 1 similarly encodes edge color 9
around outer color-5 corners and edge color 7 around inset-2 color-6 corners,
with corner-only shells at insets 1 and 3.
