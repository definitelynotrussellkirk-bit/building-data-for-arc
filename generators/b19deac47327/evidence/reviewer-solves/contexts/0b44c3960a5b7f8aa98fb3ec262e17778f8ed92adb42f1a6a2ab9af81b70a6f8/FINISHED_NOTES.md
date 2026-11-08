# Solve notes

## Hypothesis

The input has one pair of opposite solid borders, each with a different nonzero color, plus color-1 markers. For each marker, copy the nearer/assigned border color into the adjacent cell in the direction of that border while leaving the marker in place.

- Solid top/bottom borders: markers in the upper half project one cell up using the top color; markers in the lower half project one cell down using the bottom color.
- Solid left/right borders: markers in the left half project one cell left using the left color; markers in the right half project one cell right using the right color.
- On an odd-sized projection axis, the exact center belongs to the first side (top or left). Train example 1 demonstrates this at column 6 of width 13: the color is added on the left.
- Markers on an orthogonal outer edge are still processed; only the projection-axis position determines direction.

The three examples cover both orientations, both halves, an odd-axis center, and orthogonal-edge markers, so I implemented this directly without consulting any reference during the solve phase.
