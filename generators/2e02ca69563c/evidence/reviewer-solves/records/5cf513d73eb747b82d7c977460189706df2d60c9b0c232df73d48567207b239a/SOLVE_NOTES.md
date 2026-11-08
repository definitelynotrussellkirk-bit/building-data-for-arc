# Solve work log

## Exposure and constraints

This was solved from `solve-blind/challenge.json` and the public presentation only. I did not open any generator, Racket rule, canonical record, reference solution, private label, audit record, or earlier solution explanation. Earlier exposure to this task's rule: no known exposure.

## Revision 1 — exact-pair connectors inside framed rooms

The examples contain one or more hollow monochrome rectangular frames. I compared each frame independently.

Observed invariant:

- A non-frame color occurring exactly twice inside a frame is extended into a Manhattan connection.
- A color occurring once or three times is left unchanged. In train 0, color 2 occurs three times in each room and is not completed; in train 2, singleton color 2 is unchanged.
- For non-aligned endpoints, the bend is deterministic: sort endpoints by row, draw horizontally on the upper endpoint's row to the lower endpoint's column, then vertically down that column. Every diagonal pair in the three examples uses this same bend.
- Existing differently colored cells should be preserved rather than overwritten.

I first wrote a visible-example harness against the untouched stub and observed the expected `NotImplementedError`. I then implemented rectangular-ring detection using four-connected monochrome components, counted interior markers per frame, and drew the upper-row-first L for colors with exactly two markers.

Alternative considered: connect every same-colored set or complete a bounding box. This is contradicted by the three-occurrence colors, which remain unchanged, and by outputs that draw only an L rather than the whole rectangle.

Remaining uncertainty: the visible examples do not show two connector paths competing for the same blank cell. The implementation preserves an already painted different color, matching the conservative interpretation that original and earlier marker colors must not be destroyed.
