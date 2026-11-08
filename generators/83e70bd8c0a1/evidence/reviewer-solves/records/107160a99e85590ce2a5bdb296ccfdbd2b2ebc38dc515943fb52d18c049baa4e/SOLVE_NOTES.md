# Solve notes

## Revision 1

Hypothesis from the three visible pairs: the whole square grid is reflected
across the anti-diagonal.  A source cell `(r,c)` therefore moves to
`(n-1-c,n-1-r)`, while cells with `r+c=n-1` are fixed.

Visible checks used:

- In training pair 1, the `6` at `(0,0)` appears at `(5,5)`, and the `4` at
  `(5,2)` appears at `(3,0)`.
- In training pair 2, the `9` at `(0,0)` appears at `(5,5)`, while the `1` at
  `(1,4)` lies on the anti-diagonal and stays fixed.
- Differently colored occupied mirror pairs swap rather than being copied or
  overlaid, and repeated colors move by position like every other cell.

Implementation builds a fresh grid with
`out[r][c] = in[n-1-c][n-1-r]`.  No reference rule or private labels were
consulted during this solve.  I had earlier rule exposure from the generator
review, so this is intentionally recorded as an exposed, not blind, solve.
