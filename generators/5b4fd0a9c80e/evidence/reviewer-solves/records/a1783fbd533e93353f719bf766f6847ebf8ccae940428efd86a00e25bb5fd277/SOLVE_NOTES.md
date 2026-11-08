# Solve work log

I used only the visible examples produced by `review.py blind prepare`; I did not
open any generator, rule, notes, private labels, or previous solution explanation.
No earlier rule exposure is known for task `5b4fd0a9c80e`.

## Revision 1

Hypothesis: each nonzero 4-connected monochrome component is an object. Crop each
object to its bounding box, preserve any holes, sort the objects by number of
colored cells from least to greatest, and stack the crops vertically with one
blank row between them. The output width is the widest crop; narrower crops are
centered with the extra column placed on the right when the padding is odd.

Evidence from the three demonstrations:

- Object areas are `(4,4,6)`, `(4,6,7)`, and `(5,5,7)`, matching output order.
- Both equal-area cases put the narrow vertical object before the wider object,
  so I use crop width ascending (equivalently height descending in the shown ties)
  as the tie-breaker.
- Output heights equal the sum of crop heights plus two separator rows.
- Width-1 objects occupy column 1 of a 4-column output and width-3 objects occupy
  columns 0–2, matching left-biased centering.

Remaining uncertainty: the examples do not distinguish width-ascending from
height-descending for equal-area ties. Width-ascending is the simpler geometric
continuation and agrees with every visible pair.
