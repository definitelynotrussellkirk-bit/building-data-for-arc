# Solve work log

## Exposure declaration before solving

I had already reviewed this task's generator and canonical rule during the assigned
repair, so this is **not blind with respect to earlier rule exposure**. During this
solve episode itself I consulted only `challenge.json`, my own Python probes, and
the visible-only checker. I did not reopen the generator, Racket source, reference
solutions, private query labels, or earlier solution explanations after preparation.

## Revision 1 — reflect the blue shape toward aligned markers

**Hypothesis.** Color `1` is the source shape and every other nonzero color is a
marker. Process markers in zero-based row-major order. For a marker, use the first
blue cell in the same column when one exists; otherwise use the first blue cell in
the same row. Reflect every cell of the original blue shape across the midpoint
between that anchor and the marker, paint the in-bounds reflected cells with the
marker color, and retain earlier input content. Later marker paints may overwrite
earlier paints.

**Evidence from the five visible pairs.** Example 0 contains both a same-row marker
and a same-column marker and requires the two corresponding reflections. Example 1
is a pure same-column reflection. Example 3 has a marker with no usable alignment,
which produces no paint, plus a same-row marker that does. Example 4 supplies the
priority/ordering witness: the markers are adjacent, their reflected copies overlap,
and the later scan-order marker owns the overlap. Across all examples, the source
shape used for every marker is the original blue shape rather than an accumulated
painted shape, and cells outside the grid are simply absent.

**Alternatives checked.** Translating rather than reflecting gives the wrong
orientation for asymmetric source shapes. Selecting a same-row anchor before a
same-column anchor fails the both-aligned witness. Iterating newly painted cells
would create extra copies not present in the outputs. Treating marker order as
color order rather than spatial scan order disagrees with the overlap example.

**TDD record.** `WORK/checks/solve_visible_examples_test.py` first failed on the
unimplemented skeleton with `NotImplementedError`. This revision then matched all
five visible training outputs before the official visible-only check.

**Remaining uncertainty.** The visible examples determine the observed anchor
priority, scan order, clipping, and overwrite behavior, but an unseen board could
exercise multiple blue anchors in the same row or column more strongly than the
examples. The implementation follows the visible first-in-scan-order behavior.
