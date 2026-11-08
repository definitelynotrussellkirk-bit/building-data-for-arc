# Solve notes — 66387591ebe6

## Visible-example analysis

- Every grid has an integer key in the upper-left corner and one color-9 cell.
- The color-9 cell stays fixed in every output.
- Other colored cells preserve their individual colors and their rigid shape, but their source locations are cleared.
- With key 2, the object turns 90° clockwise around the 9.
- With key 3, the object turns 180° around the 9.
- With key 4, the object turns 270° clockwise (equivalently 90° counterclockwise) around the 9.
- Therefore the key encodes `key - 1` clockwise quarter-turns.  This also predicts key 1 would leave the object in place, although no key-1 visible example is present.

## Implementation

Find the unique 9 pivot, create a blank grid, preserve the upper-left key and pivot, rotate every other nonzero cell around the pivot one quarter-turn at a time, and preserve each cell's color.

## Confidence and limitations

All four visible demonstrations distinguish the direction and turn count, and the multicolor key-4 example confirms colors move cell-by-cell rather than being repainted.  I did not consult the Racket source, generator source, reference solution, or private labels during this solve phase.  I had earlier rule exposure from the required generator-review work, so this is an exposed solve rather than a blind claim.
