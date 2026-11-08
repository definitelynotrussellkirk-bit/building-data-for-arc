# Solve notes

## Visible-example hypothesis

Treat red `2` as the source marker and green `3` as the destination marker.
Compute the displacement `green - red`, create a same-sized zero grid, and
translate every cell whose color is not `0`, `2`, or `3` by that displacement.
Preserve each payload color; omit both markers and the original payload.

## Checks against the displayed examples

- Example 0: red `(2,7)` to green `(0,8)` gives `(-2,+1)`. The four `9`
  cells move from rows `2..3`, columns `4..6` to rows `0..1`, columns `5..7`.
- Example 1: red `(7,15)` to green `(9,14)` gives `(+2,-1)`. Both payload
  colors move together, which rules out recoloring or selecting only one color.
- Example 2: red `(3,9)` to green `(4,11)` gives `(+1,+2)`. This confirms the
  full marker vector rather than a fixed direction or unit step.

The examples jointly cover up-right, down-left, and down-right motion and a
multicolor payload. No crop, reflection, recoloring, or marker retention is
needed. The implementation therefore uses the direct vector translation and
fails closed if the required unique markers or in-bounds placement are absent.

## Revision history

Revision 1 implements the single rule above. No deliberately wrong teaching
attempt was submitted. I had earlier rule exposure during generator review, so
this is not claimed as a blind solve; during this solve lane I used only the
visible examples printed by `review.py solve prepare` and did not reopen a
reference rule or generator source.
