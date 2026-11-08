# Blind solve notes — cc100a8ad437

## Observations
- Every input is split by a vertical gray (`9`) line. The output has the same
  height as the input and exactly the width of the right panel.
- The left panel contains a monochrome reference shape. The right panel contains
  translated candidates in that same color, sometimes touching one another.
- A candidate is accepted only when the reference color has exactly the same
  occupancy within the reference bounding box. Same-color cells in a reference
  hole invalidate that placement; a different-colored distractor in a hole does
  not (train examples 1 and 4 demonstrate this distinction).
- Each accepted placement is rendered as the azure (`8`) perimeter of its
  bounding rectangle. For 2-cell-wide or 2-cell-high boxes, this looks filled.
- Mirrored or rotated candidates are ignored.

## Hypothesis / algorithm
1. Split at the all-`9` column.
2. Extract 4-connected monochrome reference component(s) from the left panel.
3. Slide each normalized reference mask over the right panel. Compare only
   occupancy of the reference color, allowing other colors as distractors.
4. For every exact translated match, paint the bounding-box perimeter azure;
   union overlapping perimeters on a zero background.

## Test predictions
- Query 1: matches at right-panel rows 0–1, cols 3–5 and rows 2–3,
  cols 4–6; the vertically flipped shape at rows 3–4, cols 0–2 is ignored.
- Query 2: matches at rows 2–4, cols 6–7; rows 4–6, cols 1–2; and rows
  4–6, cols 8–9. The rotated 2×3 object near the top is ignored.

## Revisions
- Revision 1 implements the hypothesis directly. No reference material or prior
  solution explanation was consulted.
