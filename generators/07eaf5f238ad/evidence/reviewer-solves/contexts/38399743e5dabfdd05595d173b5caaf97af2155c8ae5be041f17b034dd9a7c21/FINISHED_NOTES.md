# Solve notes — 07eaf5f238ad

## Revision 1

Visible examples suggest that row 0 is an ordered header and row 1 separates it
from a field of small monochrome components. Read the nonzero header tokens from
left to right. For each token, find the first four-connected body component of
that color in row-major order, crop its bounding box, and concatenate the crops
horizontally with one blank column between them.

Evidence from the visible examples:

- Train 0 has header `3,4,2,9,3`; color 9 is absent from the body and is skipped,
  while the repeated 3 causes the same first 3-crop to appear twice.
- Train 2 has a body decoy color 5 that is absent from the header and is ignored.
- Train 0 and 2 place body components in a different spatial order from the
  output, showing that header order—not scan order—controls packing.
- Crops preserve zeros inside each component's bounding box and are top-aligned.

Implementation uses same-color four-connectivity, preserves repeated header
entries, skips absent header colors, ignores non-header colors, and chooses the
first matching component. I did not open the Racket rule, generator source,
reference solution, or private labels during this solve phase. I had earlier
rule exposure from the generator repair, so the finish declaration will be yes.
