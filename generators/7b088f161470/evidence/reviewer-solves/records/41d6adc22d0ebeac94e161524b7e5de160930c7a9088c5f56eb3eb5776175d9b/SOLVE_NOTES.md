# Solve work log

## Exposure

Before this solve I had read only the packet-level instructions and the visible
presentation emitted by `python3 review.py blind prepare`. I did not inspect this
task's generator, Racket rule, reference solution, private query labels, or audit
records.

## Revision 1 — ladder summary plus farthest-marker hypothesis

The input contains four full-width nonzero horizontal baselines. Three have
ordinary colors and one is color 9. Under an ordinary baseline there may be a
three-column alternating ladder with odd height 3, 5, or 7. The visible outputs
preserve the ordinary baselines' top-to-bottom order and replace each ladder by
1, 2, or 3 copies of its color; no ladder gives an empty bar. The horizontal 9
line becomes the three-cell vertical separator in output column 3.

The isolated color-5 cell becomes a marker in output column 4. I compared its
position with the centers of the non-empty ladders. In train 1 the bottom ladder
is farthest and output row 2 is marked. In train 2 the upper of the two non-empty
ladders is slightly farther and output row 1 is marked. Train 0 has no ladders,
so all candidates are tied and the visible output uses the first row. This is a
stronger fit than nearest-object, containing-band, or simple row/column residue
hypotheses, all of which contradict at least one visible example.

Implementation: detect monochrome nonzero baselines, form each same-color
ladder from off-baseline cells, derive bar length as `(bbox_height - 1) // 2`,
and mark the non-empty ladder with greatest squared center distance from color 5
(topmost on ties; first row when all are empty).

Remaining uncertainty: the examples do not distinguish centroid distance from
bounding-box-center distance, but the ladders are symmetric so both agree here.
Both test queries have the same farthest candidate under either measure.
