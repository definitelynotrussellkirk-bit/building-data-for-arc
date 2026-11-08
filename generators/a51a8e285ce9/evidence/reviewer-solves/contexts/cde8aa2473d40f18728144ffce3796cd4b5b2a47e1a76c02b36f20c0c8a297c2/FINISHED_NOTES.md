# Post-repair visible-only solve notes

This is a human work log made after earlier exposure to the task rule during the
required generator review.  During this solve episode I consulted only
`solve/challenge.json`; I did not reopen the generator, Racket authority,
canonical labels, or any reference solution.

## Hypothesis from the four demonstrations

The two full-height separator columns divide each input into three equal panels.
The first two panels are shape prototypes and the third is a query.  Exactly one
prototype has the same occupied-cell shape as the query after a rotation and/or
reflection.  The output is **not** the query orientation: demonstration 4 makes
that clear because its query is vertically flipped relative to the returned
shape.  Instead, return the selected prototype in its displayed orientation,
tightly crop its occupied bounding box, and recolor occupied cells with the
query's foreground color.

## Implementation choices

- Derive panel width algebraically as `(input_width - 2) // 3`, rather than
  searching for color-8 columns.  This remains valid when a prototype itself is
  color 8, as in demonstrations 1 and 4.
- Compare occupied supports under all eight dihedral transforms, normalized by
  translation.
- Preserve the chosen prototype's displayed orientation, crop its bounding box,
  and use the query's sole nonzero color.

No diagnostic or intentionally wrong attempt was needed; the fourth example
resolved the only material orientation ambiguity before the first check.
