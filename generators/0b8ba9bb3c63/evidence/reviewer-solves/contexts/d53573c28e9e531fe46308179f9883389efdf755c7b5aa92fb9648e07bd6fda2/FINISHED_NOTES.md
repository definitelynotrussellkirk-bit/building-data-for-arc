# Blind solve notes — 0b8ba9bb3c63

## Initial observations

- Each example contains one solid azure (`8`) rectangle.
- The output preserves that rectangle and casts yellow (`4`) rays from every row and column occupied by it.
- Rays extend toward each grid edge through background (`0`). Red (`2`) cells are transparent to the ray and are recolored yellow.
- Any other nonzero color is opaque: the ray stops immediately before that cell, preserving the blocker and leaving cells beyond it unchanged.
- Blocking is per row or column, which explains why only the rows/columns intersecting an obstacle stop while neighboring rays continue.

## Planned implementation

Locate all `8` cells. For each occupied source row, cast left from its leftmost `8` and right from its rightmost `8`. For each occupied source column, cast up from its topmost `8` and down from its bottommost `8`. Write `4` through values `0` and `2`; stop on every other value. Preserve the source cells.

## Potential ambiguity

The examples do not show yellow in the input or a nonrectangular azure source. I treat input yellow as traversable if encountered and derive row/column extents from the actual `8` cells rather than assuming a perfect rectangle.
