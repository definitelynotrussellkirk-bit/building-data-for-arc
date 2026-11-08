# Visible-only solve notes

## Observations

- Every input is sparse and has one color-2 cell plus three to five other colored markers.
- The output discards the sparse layout and builds a rectangle. The marker with minimum row supplies the top row/color; maximum row supplies the bottom; minimum column supplies the left side; maximum column supplies the right side.
- One marker can fill two roles: train 0 has only three non-center markers, and its top marker is also the left marker.
- A non-extreme marker is irrelevant: train 2 contains two color-8 markers, but only the maximum-column one controls the right edge; the interior one disappears.
- A color-5 horizontal/vertical cross passes through the color-2 location strictly inside the frame.
- Precedence matters. Frame edges are painted before the cross/center. In train 1 the 2 lies on the top edge, so the top color covers it. At corners, observed precedence is top, then bottom, then left, then right.

## Implemented hypothesis

1. Find the first color-2 cell as the center.
2. Excluding every color-2 cell, select row-major extrema by row and column.
3. Rebuild a zero grid with the four colored frame edges.
4. Add the center and color-5 cross only where no frame edge applies.
5. Erase every other input marker.

This single rule explains all four visible pairs, including the dual-role marker, ignored extra marker, and edge-covered center.
