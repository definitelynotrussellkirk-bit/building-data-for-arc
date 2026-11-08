# Solve notes — 147c2b92e5c1

## Visible structure

Each input has one nonzero cell in row 0 and a blank row 1. Below that are three monochrome 4-connected objects. Exactly one object encloses a zero-region (a hole). The output contains only that object's color, cropped to its bounding box and doubled in both dimensions.

## Transform hypothesis from the four demonstrations

Downscaling each output by 2 makes the selected object's transform explicit:

- Example 0: row-0 code `3`; the holed color-5 object is rotated 180°.
- Example 1: code `4`; the holed color-8 object is rotated 90° counter-clockwise.
- Example 2: code `5`; the holed color-8 object is reflected left-right.
- Example 3: code `6`; the holed color-8 object is reflected up-down.

The natural completion of this ordered six-operation codebook is `1=identity` and `2=90° clockwise`. Those are the two held-out query codes. This completion is also consistent with the usual ordering identity, clockwise quarter-turn, half-turn, counter-clockwise quarter-turn, horizontal reflection, vertical reflection. I had earlier rule exposure during generator review, so this is not a blind inference claim; no reference source was consulted during this solve episode.

## Implementation

1. Read the sole nonzero code from row 0.
2. Extract same-color 4-connected body components.
3. Crop each component and flood-fill crop zeros; choose the unique component with one enclosed zero-region.
4. Apply the code transform.
5. Replace every transformed cell with a 2×2 block.

The code handles touching objects of different colors as separate components, matching a visible/canonical edge case encountered during repair.
