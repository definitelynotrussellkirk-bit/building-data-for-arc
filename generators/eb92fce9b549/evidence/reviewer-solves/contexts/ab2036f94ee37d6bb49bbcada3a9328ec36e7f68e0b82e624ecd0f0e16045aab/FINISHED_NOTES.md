# Fresh solve notes

## Visible evidence

All outputs erase the original nonzero color identity and repaint each 4-connected nonzero object with consecutive colors starting at 2. The largest-ranked object receives 2, the next receives 3, and so on.

The decisive comparison is the second and third demonstrations. The sparse L-shaped object occupies five cells in a 3×3 bounding box, while the filled 2×3 rectangle occupies six cells. The L receives color 2 and the rectangle receives color 3. Therefore occupied-cell count is not the ranking statistic; descending bounding-box area (9 before 6) fits both demonstrations. The vertical line in demonstration two has bounding-box area 4 and receives color 4, completing the order 9, 6, 4.

The nested-frame demonstration is also consistent: outer frames have larger bounding boxes than inner frames and are assigned lower output colors.

## Hypotheses considered

1. **Rank by occupied-cell count.** Rejected: the six-cell 2×3 rectangle loses to the five-cell sparse 3×3 object.
2. **Rank by scan order or position.** Rejected: object positions vary, while the 9→6→4 bounding-box-area sequence remains exact.
3. **Rank by bounding-box area descending.** Retained. Extract same-color 4-connected nonzero components, sort by `(height × width)` descending, blank the canvas, and repaint ranks as 2, 3, 4, ….

## Implementation decision

Use a four-neighbor flood fill that requires the same source color, compute each component's bounding box, and sort by descending area. Visible examples have unique areas. A top-left tie-breaker is included only to make the implementation deterministic; no claim is made about unseen equal-area ties.
