# Post-repair visible-only solve notes

Earlier exposure is **yes** because I reviewed this task's generator and canonical rule before this required solve. During the solve phase itself I used only the prepared visible examples and did not reopen the generator, Racket source, prior solution, or private labels.

## Hypothesis from the examples

- The two nonzero cells at `(0,0)` and `(0,1)` are ordered operation codes.
- Remove those two cells before finding objects.
- The connected object made of color 9 is the prototype; every other isolated colored singleton is a stamp anchor and supplies the output color.
- Crop the prototype to its tight binary bounding box, apply the two operations in order, then center the transformed binary shape on every anchor in a blank same-size output. Crop any cells falling outside the grid.

## Operation code evidence

- Example 0 (`2,4`) maps the prototype through left-right reflection followed by a clockwise quarter-turn; the resulting `001 / 101 / 111` pattern appears at each anchor.
- Example 1 (`4,3`) is consistent with clockwise rotation followed by top-bottom reflection.
- Example 2 (`2,6`) confirms code 6 as counterclockwise rotation after code 2's left-right reflection.
- I use the natural remaining mapping: 1 identity, 5 half-turn, and unknown/out-of-range codes as identity. The visible queries need only `(6,3)` and `(2,4)`.

## Implementation choices

- Components use 4-connectivity.
- Anchor order is row-major component discovery; non-overlapping visible examples make order irrelevant, while retaining it handles possible overlap deterministically.
- Even-sized transformed shapes use integer-floor centering, matching the visible placements.
