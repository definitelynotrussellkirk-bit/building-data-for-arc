# Visible-only solve notes

## Hypothesis

The nonzero cells form separate monochrome 4-connected objects. Each output is
made from the tight bounding-box crop of each object, preserving its orientation
and internal zeros. The crops are sorted by **occupied cell count, largest to
smallest**, then stacked vertically. A single all-zero row separates neighboring
crops; every crop is left-aligned in an output whose width is the widest crop.

## Evidence from the four visible pairs

- Pair 1 has object areas 5, 4, and 3. Its output order is 5-cell color 4,
  4-cell color 1, then 3-cell color 3, even though that is not input scan order.
- Pair 2 has areas 5, 4, and 3 and again uses descending occupied area. The
  5-cell color-3 crop precedes the 4-cell color-5 crop and 3-cell color-8 crop.
- Pair 3 demonstrates four objects and an output width of three. The 8-cell
  object appears before the 6-, 4-, and 2-cell objects, with exactly one blank
  row between crops.
- Pair 4 independently confirms four-object retention, left alignment, and
  order 8, 6, 4, 2 by occupied area.

## Alternatives rejected from visible evidence

Input scan order, color order, smallest-first order, omitting the fourth object,
centering narrow crops, and omitting separator rows all contradict at least one
visible pair. Bounding-box area is also not needed to explain the examples;
occupied-cell count explains every ordering consistently.

## Implementation

Flood-fill same-color cells using four-neighbor connectivity, compute each tight
crop and occupied area, sort descending by occupied area, and concatenate padded
crops with one zero separator row.

I had earlier exposure to this task's rule during generator review, so this is
not claimed as a blind solve. During this solve episode I consulted only the
visible challenge and did not reopen the generator, Racket rule, labels, or
reference explanations.
