# Visible-only solve notes: `a7e26e20850c`

## Evidence used

Only the four labeled examples and two unlabeled query inputs printed by
`review.py solve prepare` were used during this solve. I did not reopen the
Racket rule, generator, canonical records, prior solution text, or private labels.
I had already seen the task rule during the earlier generator-review phase, so
this is intentionally recorded as **earlier exposure: yes**, not as a blind solve.

## Hypothesis

The top row is a legend. Each maximal same-color nonzero run gives a mapping
from **run length** to **run color**. The blank second row separates the legend
from the body. Each 4-connected gray (color 5) body object is recolored to the
legend color whose run length equals that object's cell count. Zeros and the
legend itself remain unchanged.

Checks against the visible examples:

- Example 0 has legend sizes 5→8 and 2→1. Its gray components have sizes 5, 2,
  and 5, and the outputs use 8, 1, and 8 respectively.
- Example 1 has sizes 5→8, 3→6, 4→9, 2→1; the three body components of sizes
  2, 4, and 3 become 1, 9, and 6.
- Examples 2 and 3 confirm that geometry and position do not select the color;
  only the connected component's cell count does.

## Implementation decisions

- Parse maximal same-color runs rather than assuming fixed starts or gaps.
- Use 4-neighbor connectivity for gray components, matching every visible
  object and avoiding accidental diagonal merging.
- Raise on a missing or contradictory legend entry instead of silently making
  a guess.
- Preserve the input by returning a deep-copied output.

## Query predictions

- Query 0: both size-2 vertical objects become color 3; the size-3 L becomes
  color 1.
- Query 1: size-2 becomes 6, size-4 becomes 4, and size-5 becomes 7.
