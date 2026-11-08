# Solve notes

## Revision 1 — square-ring parity

Across the visible examples, the 3s form a complete rectangular frame plus one
interior 3 marker. The output preserves every 3 and every exterior 0. Interior
0s become concentric axis-aligned square rings centered on the marker: a cell's
ring number is its Chebyshev distance `max(|dr|, |dc|)`. Even distances are 2
and odd distances are 4. The bounding box of all 3s locates the frame because
the marker lies strictly inside it; the sole interior 3 locates the center.
This also handles markers touching a ring/frame diagonally or orthogonally.
