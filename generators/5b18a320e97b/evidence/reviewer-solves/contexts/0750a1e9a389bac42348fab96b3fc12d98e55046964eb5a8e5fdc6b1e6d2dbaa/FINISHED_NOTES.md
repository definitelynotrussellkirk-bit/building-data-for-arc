# Solve work log

I had no earlier exposure to task `5b18a320e97b`, its generator, its Racket
rule, private labels, or prior solution explanations. I used only the visible
examples produced by `review.py blind prepare`.

## Revision 1 — compress ordered guide lines

Hypothesis: the solid color-5 square is a mask whose side length is the output
side length. Every other nonzero color forms one horizontal or vertical guide
line. Some guide lines are complete; others are truncated or hidden where the
5-square lies. The output preserves those guide-line colors in spatial order
and expands each into a full stripe: horizontal input lines become output rows,
and vertical input lines become output columns.

Evidence from the visible examples:

- Example 0 has a 7×7 square of 5s and seven horizontal guide colors at
  increasing row positions. The output is seven solid rows in exactly that
  order.
- Examples 1 and 2 have 5×5 and 3×3 squares and respectively five and three
  vertical guide colors. Their outputs are solid columns ordered left-to-right.
- Query 0 appears vertical with six colors, including lines partially hidden by
  the 6×6 square; query 1 appears horizontal with six colors.

Implementation: locate and validate the solid 5-square, collect coordinates for
each other nonzero color, infer the common orientation from coordinate spans,
sort colors by their row or column, and emit the corresponding square of full
stripes. Remaining uncertainty: the visible data always uses one unique color
per guide line and exactly one guide line per output stripe; the solver treats
those as task invariants.
