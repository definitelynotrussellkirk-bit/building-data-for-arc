# Post-repair visible-only solve notes

The three visible examples all remove the all-zero border surrounding the full
set of colored cells.  The resulting tight rectangle is then transposed: an
`h × w` crop becomes `w × h`, and internal zeros stay in their corresponding
transposed positions.  Colors are copied unchanged.  The second and third
examples show that separated groups are not processed independently; one bbox
around all nonzero cells is used.

Implemented one direct hypothesis: collect all nonzero coordinates, crop from
their minimum to maximum row/column, then transpose that crop.  No reference
solution or Racket rule was consulted during this solve phase.  I had already
seen the rule while repairing the generator, so this is explicitly an exposed
post-repair solve rather than a blind solve.
