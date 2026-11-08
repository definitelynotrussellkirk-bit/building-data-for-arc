# Solve work log

## Exposure

Before this solve I had read only packet-level instructions and repository-level documentation. I had not opened task `a4863798ed70`'s generator, Racket rule, canonical row, notes, prior solutions, or private labels.

## Revision 1 — cyclic payload-color transfer

Visible examples contain several rectangular frames made from color 2. Each frame encloses a single irregular payload shape whose cells all share one color. The shape and frame locations are unchanged in the output; only the payload colors move.

Ordering the frame centers clockwise around their common centroid gives a cycle. Every frame receives the payload color of the next clockwise frame. This explains all visible pairs:

- three-frame example: top <- right <- bottom <- top;
- four-frame example: top <- right <- bottom <- left <- top;
- five-frame example: upper-left <- upper-right <- right-middle <- bottom <- left-middle <- upper-left.

Implementation probe: detect 4-connected color-2 components whose bounding-box perimeter is complete, collect each frame's interior non-background payload cells, sort frame centers by `atan2(row-centroid, col-centroid)` (clockwise in image coordinates), and recolor each payload shape with the next frame's color. The implementation intentionally preserves payload geometry, color-1 wiring, color-2 frames, and all zero cells.

Remaining uncertainty: this assumes each box has one payload color and that the frame centers form one cyclic spatial ordering. Both properties hold in all visible examples and queries.
