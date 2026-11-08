# Solve work log

## Exposure before solving

I had not opened the task's generator, canonical rule, reference solutions,
private labels, prior solution explanations, my assigned repair generator, or
audit evidence. I used only the visible examples produced by `blind prepare`.

## Hypothesis and observations

The colored singleton cells in column 0 are a palette, read top to bottom. The
remaining non-background cells are color-3 shapes. Treat each 4-connected gray
shape as one object, rank the objects by cell count from largest to smallest,
and pair those ranked objects with the palette colors in order.

For each object, take its tight bounding-box crop, replace every gray cell by
its paired palette color, and left-align the crops in a common output width.
Stack the crops vertically with one all-zero separator row. This explains why
training output height is not simply three rows per object: in example 0 the
object heights are 2, 3, and 2, plus two separator rows, totaling 9.

The visible examples have distinct object areas. I use top-left position only as
a deterministic tie-breaker; the examples do not establish the intended rule
for equal-area objects.

## Probe history

1. Wrote a visible-training regression harness against `challenge.json` before
   implementing the solver. It failed at the starter `NotImplementedError`, as
   expected.
2. Implemented 4-neighbor component extraction, descending-area ranking, tight
   crops, recoloring, common-width left alignment, and zero-row separators.
3. Next checks: rerun the visible-training harness and the packet's blind check.
