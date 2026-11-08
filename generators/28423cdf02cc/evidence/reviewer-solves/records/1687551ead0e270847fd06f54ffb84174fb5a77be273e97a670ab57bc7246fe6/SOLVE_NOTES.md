# Solve work log

## Prior exposure

Before this solve I had read only the packet-level instructions and the visible
examples printed by `python3 review.py blind prepare`. I did not open this task's
generator, rule, notes, reference solution, audit records, or private labels.

## Hypothesis

The upper-left 3×3 block is a colored key or stamp. The solid color-5 column at
column 3 separates that key from a blank canvas. Every color-1 cell on the canvas
marks the **center** of a location where an unchanged copy of the 3×3 key should
be painted.

Evidence from the visible examples:

- In train 0, marker `(1, 5)` becomes the key over rows `0..2`, columns `4..6`;
  marker `(7, 11)` becomes the same key over rows `6..8`, columns `10..12`.
- In train 2, marker `(2, 6)` becomes a key over rows `1..3`, columns `5..7`,
  while marker `(12, 14)` becomes one over rows `11..13`, columns `13..15`.
- The separator and original upper-left key remain unchanged. There is no
  rotation, recoloring, reflection, or dependence on marker order.

## Implementation

Copy the grid, save `grid[0:3][0:3]` as the key, collect all original color-1
coordinates, and overlay the key with its center at each marker. Marker
coordinates are collected before painting so one placement cannot affect which
markers are processed. Bounds checks make the function total, although every
visible marker is one cell away from the outer border as required for a full
3×3 copy.

## Remaining uncertainty

The visible data strongly fixes the key size, location, marker color, and center
alignment. A more abstract detector for a differently sized key is possible, but
would add unsupported behavior: every visible instance uses exactly the same
3×3-at-top-left layout. I therefore implemented the narrowest rule consistent
with all demonstrations.
