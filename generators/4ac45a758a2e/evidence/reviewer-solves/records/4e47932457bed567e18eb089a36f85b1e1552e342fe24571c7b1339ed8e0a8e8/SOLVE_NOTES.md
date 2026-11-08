# Solve notes

This is a human work log based on the prepared visible examples. I did not open
or consult the Racket rule, generator source, reference solution, or private
query labels during this solve. I had already reviewed the generator before the
fresh episode, so earlier rule exposure must be recorded as **yes**.

## Observations and hypothesis

- The input is copied unchanged except for a cyan (8) copy of the magenta (6)
  object placed at the orange (7) marker.
- The cyan copy preserves the number of magenta cells. The orange marker acts as
  the top-left origin of the transformed object's normalized bounding box; it is
  overwritten when the transformed object contains normalized coordinate (0,0).
- Across examples 0--3, the number of blue cells is 1, 2, 3, 4 and selects 0,
  90, 180, 270 degrees clockwise respectively.
- Across examples 4--7, two red cells add a left-right reflection after the
  blue-selected rotation. One red cell means no reflection.
- The object must be normalized after each transform because its original
  absolute location is irrelevant.

## Implementation decision

Extract all color-6 coordinates, normalize them, rotate clockwise
`blue_count - 1` times, horizontally reflect when `red_count == 2`, normalize
again, and paint the resulting coordinates in color 8 relative to the single
orange cell. Preserve all other cells.
