# Blind solve notes — d377a54f20c6

## Visible-example hypothesis

Each nonzero 4-connected component is a solid, axis-aligned rectangle with one
minority-color marker.  The marker's *position* is discarded; its color becomes
the drawing color.  The majority color remains only as the rectangle's one-cell
frame.  The original interior is cleared to background and replaced by the
centered inset-X / rectangular medial skeleton obtained by tracing 45-degree
lines inward from the four interior corners.  When the interior is wider than
it is tall, the two diagonals are joined by a horizontal center bridge; when it
is taller, by a vertical center bridge.

This accounts for:

- the 5x5 interior becoming an ordinary X;
- the 7x11 and 8x11 interiors gaining a horizontal middle segment;
- the 8x6 interior gaining a vertical middle segment;
- the minority cell's varying location having no effect beyond choosing color.

## Implementation probe

I identify the modal grid color as background, find non-background 4-connected
components, infer majority/minority colors within each component, and reconstruct
the frame plus inset-X skeleton from the component bounding box.  The geometric
predicate uses distance to the nearest horizontal and vertical interior edge;
equal distances trace the diagonals, and cells at the exhausted shorter-axis
center extend the bridge along the longer axis.
