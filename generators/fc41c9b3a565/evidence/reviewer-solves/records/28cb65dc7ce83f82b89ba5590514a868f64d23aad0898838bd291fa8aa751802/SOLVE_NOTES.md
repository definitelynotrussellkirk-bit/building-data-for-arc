# Visible-only solve notes

## Observation

Every output has the same dimensions as its input and is made only by deleting whole, same-colored 4-connected components. Surviving cells keep both their coordinates and color. Different colors can touch (train 3), so components must be tracked per color rather than by nonzero connectivity alone.

## Candidate rules considered

1. Keep the largest or most frequent shape. This fails train 1, where two five-cell components survive and another five-cell component is erased.
2. Keep squares or shapes symmetric under a vertical/horizontal reflection. The 2x2 square survives, but train 1's color-8 zigzag and train 3's color-1 zigzag are not mirror-symmetric across either axis.
3. Keep components whose cropped occupied-cell mask is unchanged by a 180-degree turn. This explains every label:
   - train 0 keeps the 2x2 square and drops all three L triominoes;
   - train 1 keeps the plus and the five-cell point-symmetric zigzag, while dropping the one-axis-symmetric T-like decoy;
   - train 2 keeps only the five-cell point-symmetric zigzag;
   - train 3 keeps the same zigzag morphology even though its color and position changed.

## Implementation

For each nonzero color, find each 4-connected component. Translate its cells so the component bounding box begins at `(0, 0)`. Rotate every normalized cell `(r, c)` to `(H-1-r, W-1-c)`. Preserve the component iff the rotated set equals the original set; otherwise leave its cells as background 0.

## Query predictions

- Query 0: keep colors 1 and 8; erase color 7.
- Query 1: keep the 2x2 color-7 square and the four-cell color-9 point-symmetric zigzag; erase color 5.

Earlier exposure is necessarily **yes** because this solve follows the generator review. I did not consult the generator, Racket rule, reference solution, private labels, or prior solve notes during this solve.
