# Solve notes — ebff81ea3252

## Visible-example hypothesis

The output recolors color-3 cardinal crosses to color 7. A cross is recognized
locally: an interior cell and its north, south, west, and east neighbors must
all be 3 in the original input. Exactly those five cells become 7. Extra green
cells attached diagonally/corner-adjacent to the cross remain 3, so connected
component size is not the criterion.

Evidence from the visible examples:
- Train 1 has a six-cell component at the left: the five cross cells become 7
  while the extra upper-left green cell remains 3.
- Train 2 contains two isolated crosses, both recolored, while the separate
  five-cell non-cross cluster remains green.
- Train 3 contains attached crosses; only the local cross cells change and the
  attached corner cells remain green.

Implementation plan: find every qualifying center in the unchanged input, copy
the grid, then recolor the union of each center and its four cardinal neighbors.
The detection pass must not read already-modified output cells.
