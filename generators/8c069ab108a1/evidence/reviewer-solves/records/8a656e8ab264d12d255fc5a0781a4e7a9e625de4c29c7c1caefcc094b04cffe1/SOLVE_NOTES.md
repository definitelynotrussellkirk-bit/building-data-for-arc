# Visible-example solve notes

## Hypothesis

Color 9 is the unique rotation center and is not copied into the output. For
each other colored input cell, preserve its color and stamp it at the four
quarter-turn positions around that center: 0°, 90°, 180°, and 270°. The output
has the same dimensions and otherwise contains zero.

## Evidence from the visible examples

- In example 0, each of the two color-8 cells expands to four positions, giving
  exactly eight output cells, while color 9 disappears.
- Examples 1 and 2 show that the operation is applied independently to every
  colored cell and preserves multiple colors.
- The anchor is off center in examples 1 and 2, so the center must be the
  observed color-9 cell rather than the geometric grid center.

## Implementation

Locate the sole 9, convert every nonzero/non-9 cell to an offset from it, and
iterate `(dr, dc) -> (dc, -dr)` four times. Only in-bounds positions are written.
