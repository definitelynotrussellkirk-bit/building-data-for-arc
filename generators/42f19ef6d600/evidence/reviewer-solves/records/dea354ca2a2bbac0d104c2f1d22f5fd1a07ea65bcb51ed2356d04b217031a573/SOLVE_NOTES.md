# Blind solve notes — 42f19ef6d600

## Visible observations

- Color 7 is the background in every visible example.
- The output leaves all source objects unchanged and adds color 2 only around connected components whose bounding boxes are nontrivial squares.
- Isolated pixels, a 1×4 line, and a 2×4 rectangle are not changed.
- Solid 2×2, 3×3, and 4×4 squares receive a complete one-cell outside border, excluding diagonal corner cells.
- Hollow square frames receive only the outside positions supported by the next row/column inward. For the visible 4×4 hollow frame, the top outside row is copied from its second row (`8 7 7 8`), so only the two endpoints become 2. The same relation holds on all four sides and for the 3×3 ring.

## Hypothesis

For every 4-connected non-background component with a square bounding box of side at least two, extrapolate one layer outward. The new top/bottom border copies occupancy from the second/penultimate component row, and the new left/right border copies occupancy from the second/penultimate component column. Write color 2 only into background cells.

This explains every visible change and rejects all visible distractors. It also predicts that the two test cases repeat the demonstrated combinations: three square components in query 0 and one solid square plus a line distractor in query 1.

## Implementation notes and limitations

- Background is inferred as the modal input color rather than hard-coded to 7.
- Components are separated by both color and 4-connectivity.
- A 1×1 component is deliberately excluded because visible singletons are distractors.
- The examples do not distinguish this extrapolation description from a more specialized rule that recognizes only filled squares and one-cell square frames. The implementation uses the broader local relation directly evidenced by the outputs.
