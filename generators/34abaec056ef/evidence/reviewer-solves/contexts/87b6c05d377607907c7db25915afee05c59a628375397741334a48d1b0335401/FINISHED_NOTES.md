# Solve work log

## Prior exposure

Before this solve I had not opened task `34abaec056ef`'s generator, canonical
rule, notes, reference solutions, private query labels, or audit evidence.  I
used only the visible examples printed by `python3 review.py blind prepare` and
the generated `challenge.json`.

## Revision 1 — local coordinate frame

Hypothesis: color 2 is an origin, color 4 defines the positive output-row axis,
and color 3 defines the positive output-column axis.  The 3×3 answer is the
mask of color-8 cells at local coordinates `(row, column) ∈ {-1,0,1}²`, shifted
by `(1,1)`.  Other colors and color-8 cells outside that local window are
distractors.

Evidence from the visible pairs:

- Example 3 already has 3 to the right of 2 and 4 below 2, so the two 8s at
  offsets `(-1,-1)` and `(-1,+1)` appear unchanged at output cells `(0,0)` and
  `(0,2)`.
- Examples 0 and 2 use the same two input offsets for their 8s but swap the
  locations of markers 3 and 4; their output changes from a vertical domino to
  a horizontal domino exactly as this coordinate-frame interpretation predicts.
- Example 1 has one 8 two local steps from the origin; excluding it explains
  why only two of the three input 8s appear.

Probe: a temporary visible-only regression script loads all four training pairs
from `challenge.json`.  It first failed on the untouched `NotImplementedError`,
then was rerun after implementing the frame transform.

Predicted query masks before checking:

- Query 0: 8 at output `(0,0)` and `(2,2)`.
- Query 1: 8 at output `(1,0)` and `(2,0)`; the distant third 8 is ignored.

Alternative considered: crop an axis-aligned 3×3 neighborhood around color 2.
That fails examples 0 and 2 because their outputs rotate/reflect with markers 3
and 4.  Remaining uncertainty is limited to malformed inputs with duplicated or
collinear frame markers; the visible task consistently uses one of each and an
orthogonal frame.
