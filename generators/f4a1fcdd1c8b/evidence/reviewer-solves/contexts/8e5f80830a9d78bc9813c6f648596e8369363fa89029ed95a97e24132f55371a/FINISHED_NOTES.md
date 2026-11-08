# Solve work log

## Exposure record

Before this solve I had not opened this task's generator, Racket rule, notes,
reference solutions, private query labels, or audit records. I used only the
visible challenge and my own feature inspection.

## Revision 1 — boundary-connected-object hypothesis

Across all three demonstrations, every retained nonzero 4-connected object
intersects at least one outer row or outer column. Every removed object is
strictly interior. This also explains the important same-color case in train 1:
the large color-9 component reaches the left edge and remains, while the
separate interior color-9 component is deleted. Shape, area, and color therefore
appear to be distractors.

I first ran the visible-example assertion harness against the supplied stub and
observed the expected `NotImplementedError` failure. I then implemented a
same-color 4-neighbor flood fill, independently preserving a component iff any
of its cells lies on the grid boundary. This predicts mixed treatment of
separate components sharing a color and avoids treating diagonal contact as
connectivity.

Remaining uncertainty is limited to whether an unseen case could use a
nonzero background or 8-connectivity, but all visible examples consistently use
zero background and clearly separated 4-connected objects. No reference source
was consulted.
