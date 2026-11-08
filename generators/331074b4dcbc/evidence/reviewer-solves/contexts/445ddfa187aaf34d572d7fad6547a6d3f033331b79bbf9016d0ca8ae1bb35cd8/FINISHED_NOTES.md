# Blind solve notes

The first row is a color key: its consecutive nonzero prefix has length two or
three in the visible examples.  Elsewhere, a solid rectangular region of 8s is
a canvas.  The output preserves the key and all zeros, while replacing each row
of the rectangle with the key repeated left-to-right, anchored at the
rectangle's left edge.  The phase restarts identically on every rectangle row.

Probe against the three demonstrations:
- `[4,6]` over width 7 gives `4,6,4,6,4,6,4`.
- `[8,6,1]` over width 7 gives `8,6,1,8,6,1,8`; therefore 8 may itself be a key color.
- `[2,7,9]` over width 7 gives `2,7,9,2,7,9,2` independent of absolute column.

Implementation copies the grid, extracts the row-0 prefix through the first
zero, locates non-header 8 cells, anchors at their minimum column, and colors
those cells by `(column-left) mod key_length`.  I expect this to handle both
visible test rectangles, including the width-8 case.
