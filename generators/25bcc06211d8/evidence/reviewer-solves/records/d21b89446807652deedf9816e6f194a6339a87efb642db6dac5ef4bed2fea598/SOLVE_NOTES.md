# Blind solve notes — 25bcc06211d8

## Boundary

I read only `solve-blind/challenge.json` while deriving this solution. I did not
open the generator, canonical rule, reference solutions, task notes, private
labels, audit records, or the assigned repair target.

## Visible pattern

Each nonzero color is a separate 4-connected polyomino. The output keeps the
color, component bounding box, cell count, and the apparent long spine, while
moving end-attached cells toward the center of that spine:

- Every five-cell example has a three-cell vertical spine plus one protrusion
  at each end. The two protrusions move to opposite sides of the middle spine
  cell, producing a centered plus in the same 3x3 box.
- Every four-cell example has a length-three horizontal or vertical spine and
  one protrusion attached at one end. The protrusion slides to the midpoint on
  the same side, producing a T in the same 2x3 or 3x2 box.
- The only three-cell example is a 2x2 L missing its upper-left corner; its
  output is the upper-left L (missing the lower-right corner). With only one
  example this orientation rule is underdetermined, so the implementation
  records the narrowest literal normalization that matches it.

The two test inputs contain only four- and five-cell components, so their
predictions do not depend on the ambiguous triomino case.

## Implementation decision

Use 4-connected monochromatic components, classify by cell count and bounding
box, and draw the corresponding centered plus/T/L. Preserve unrecognized
components unchanged rather than extrapolating an unsupported transformation.

## Predicted query behavior

- Test 1: both five-cell components become pluses centered at their existing
  vertical-spine midpoint.
- Test 2: colors 8 and 3 become pluses; color 9 becomes a downward-pointing T
  with the lower cell centered beneath its three-cell top row.
